from typing import Dict, List, Optional, Any, Tuple, Callable
import logging
import time
import json
from enum import Enum

logger = logging.getLogger(__name__)

class NegotiationStatus(Enum):
    """协商状态枚举"""
    PENDING = 0
    ACCEPTED = 1
    REJECTED = 2
    COUNTEROFFERED = 3
    TIMEOUT = 4
    FAILED = 5

class NegotiationType(Enum):
    """协商类型枚举"""
    TASK_ALLOCATION = 0  # 任务分配
    RESOURCE_SHARING = 1  # 资源共享
    INFORMATION_REQUEST = 2  # 信息请求
    COORDINATION = 3  # 行动协调
    CUSTOM = 99  # 自定义

class Negotiator:
    """
    协商机制，处理智能体之间的协商过程
    """
    
    def __init__(self, agent_id: str, comm_manager: Any):
        """
        初始化协商器
        
        Args:
            agent_id: 智能体ID
            comm_manager: 通信管理器实例
        """
        self.agent_id = agent_id
        self.comm_manager = comm_manager
        self.negotiations: Dict[str, Dict[str, Any]] = {}  # 协商ID到协商记录的映射
        self.active_negotiations: Dict[str, Dict[str, Any]] = {}  # 当前活跃的协商
        self.handlers: Dict[NegotiationType, Callable] = {}  # 协商类型到处理函数的映射
        self.default_timeout = 30  # 默认超时时间(秒)
        self.next_negotiation_id = 1
    
    def register_handler(self, negotiation_type: NegotiationType, handler: Callable) -> None:
        """
        注册协商类型的处理函数
        
        Args:
            negotiation_type: 协商类型
            handler: 处理函数，接收(negotiation_data, sender_id)参数
        """
        self.handlers[negotiation_type] = handler
    
    def start_negotiation(self, 
                         target_id: str, 
                         negotiation_type: NegotiationType, 
                         content: Any, 
                         timeout: Optional[float] = None) -> str:
        """
        发起协商
        
        Args:
            target_id: 目标智能体ID
            negotiation_type: 协商类型
            content: 协商内容
            timeout: 超时时间(秒)
            
        Returns:
            str: 协商ID
        """
        negotiation_id = f"{self.agent_id}_{self.next_negotiation_id}"
        self.next_negotiation_id += 1
        
        # 创建协商记录
        negotiation = {
            "id": negotiation_id,
            "initiator": self.agent_id,
            "target": target_id,
            "type": negotiation_type.value,
            "content": content,
            "status": NegotiationStatus.PENDING.value,
            "start_time": time.time(),
            "timeout": timeout or self.default_timeout,
            "responses": [],
            "result": None
        }
        
        # 保存记录
        self.negotiations[negotiation_id] = negotiation
        self.active_negotiations[negotiation_id] = negotiation
        
        # 发送协商消息
        message = {
            "action": "negotiation_request",
            "negotiation_id": negotiation_id,
            "type": negotiation_type.value,
            "content": content
        }
        
        success = self.comm_manager.send_message(self.agent_id, target_id, json.dumps(message))
        if not success:
            negotiation["status"] = NegotiationStatus.FAILED.value
            if negotiation_id in self.active_negotiations:
                del self.active_negotiations[negotiation_id]
        
        return negotiation_id
    
    def check_timeout(self) -> List[str]:
        """
        检查并处理超时的协商
        
        Returns:
            List[str]: 超时的协商ID列表
        """
        now = time.time()
        timed_out = []
        
        for negotiation_id, negotiation in list(self.active_negotiations.items()):
            start_time = negotiation.get("start_time", 0)
            timeout = negotiation.get("timeout", self.default_timeout)
            
            if now - start_time > timeout:
                negotiation["status"] = NegotiationStatus.TIMEOUT.value
                timed_out.append(negotiation_id)
                del self.active_negotiations[negotiation_id]
        
        return timed_out
    
    def handle_message(self, sender_id: str, message_str: str) -> bool:
        """
        处理接收到的协商消息
        
        Args:
            sender_id: 发送者ID
            message_str: 消息内容(JSON字符串)
            
        Returns:
            bool: 是否成功处理
        """
        try:
            message = json.loads(message_str)
            action = message.get("action", "")
            
            if action == "negotiation_request":
                return self._handle_request(sender_id, message)
            elif action == "negotiation_response":
                return self._handle_response(sender_id, message)
            else:
                logger.warning(f"未知协商动作: {action}")
                return False
                
        except json.JSONDecodeError:
            logger.error(f"无法解析协商消息: {message_str}")
            return False
        except Exception as e:
            logger.exception(f"处理协商消息时出错: {e}")
            return False
    
    def _handle_request(self, sender_id: str, message: Dict[str, Any]) -> bool:
        """处理协商请求"""
        negotiation_id = message.get("negotiation_id", "")
        negotiation_type = message.get("type")
        content = message.get("content")
        
        if not negotiation_id:
            return False
        
        # 查找对应类型的处理函数
        negotiation_type_enum = NegotiationType(negotiation_type) \
            if isinstance(negotiation_type, int) else NegotiationType.CUSTOM
            
        handler = self.handlers.get(negotiation_type_enum)
        
        if handler:
            # 调用处理函数处理请求
            try:
                result = handler(content, sender_id)
                # 发送响应
                self._send_response(negotiation_id, sender_id, result)
                return True
            except Exception as e:
                logger.exception(f"处理协商请求时出错: {e}")
                self._send_response(negotiation_id, sender_id, {
                    "status": NegotiationStatus.FAILED.value,
                    "reason": f"处理出错: {str(e)}"
                })
                return False
        else:
            # 没有对应处理函数，默认拒绝
            logger.warning(f"未找到协商类型 {negotiation_type} 的处理函数")
            self._send_response(negotiation_id, sender_id, {
                "status": NegotiationStatus.REJECTED.value,
                "reason": "未处理的协商类型"
            })
            return False
    
    def _handle_response(self, sender_id: str, message: Dict[str, Any]) -> bool:
        """处理协商响应"""
        negotiation_id = message.get("negotiation_id", "")
        status = message.get("status")
        content = message.get("content")
        
        if not negotiation_id or negotiation_id not in self.negotiations:
            logger.warning(f"未知协商ID: {negotiation_id}")
            return False
        
        negotiation = self.negotiations[negotiation_id]
        
        # 记录响应
        response = {
            "sender_id": sender_id,
            "status": status,
            "content": content,
            "time": time.time()
        }
        
        negotiation["responses"].append(response)
        
        # 更新协商状态
        if status == NegotiationStatus.ACCEPTED.value:
            negotiation["status"] = NegotiationStatus.ACCEPTED.value
            negotiation["result"] = content
            if negotiation_id in self.active_negotiations:
                del self.active_negotiations[negotiation_id]
        elif status == NegotiationStatus.REJECTED.value:
            negotiation["status"] = NegotiationStatus.REJECTED.value
            if negotiation_id in self.active_negotiations:
                del self.active_negotiations[negotiation_id]
        elif status == NegotiationStatus.COUNTEROFFERED.value:
            negotiation["status"] = NegotiationStatus.COUNTEROFFERED.value
        
        return True
    
    def _send_response(self, negotiation_id: str, target_id: str, result: Dict[str, Any]) -> bool:
        """发送协商响应"""
        message = {
            "action": "negotiation_response",
            "negotiation_id": negotiation_id,
            "status": result.get("status", NegotiationStatus.REJECTED.value),
            "content": result.get("content")
        }
        
        return self.comm_manager.send_message(self.agent_id, target_id, json.dumps(message))
    
    def get_negotiation_status(self, negotiation_id: str) -> Tuple[NegotiationStatus, Optional[Any]]:
        """
        获取协商状态
        
        Args:
            negotiation_id: 协商ID
            
        Returns:
            Tuple[NegotiationStatus, Optional[Any]]: (协商状态, 结果)
        """
        if negotiation_id not in self.negotiations:
            return NegotiationStatus.FAILED, None
            
        negotiation = self.negotiations[negotiation_id]
        status = NegotiationStatus(negotiation["status"])
        return status, negotiation.get("result")
    
    def accept_negotiation(self, negotiation_id: str, content: Any = None) -> bool:
        """
        接受协商
        
        Args:
            negotiation_id: 协商ID
            content: 响应内容
            
        Returns:
            bool: 是否成功
        """
        if negotiation_id not in self.negotiations:
            return False
            
        negotiation = self.negotiations[negotiation_id]
        
        message = {
            "action": "negotiation_response",
            "negotiation_id": negotiation_id,
            "status": NegotiationStatus.ACCEPTED.value,
            "content": content
        }
        
        return self.comm_manager.send_message(
            self.agent_id, negotiation["initiator"], json.dumps(message))
    
    def reject_negotiation(self, negotiation_id: str, reason: str = "") -> bool:
        """
        拒绝协商
        
        Args:
            negotiation_id: 协商ID
            reason: 拒绝原因
            
        Returns:
            bool: 是否成功
        """
        if negotiation_id not in self.negotiations:
            return False
            
        negotiation = self.negotiations[negotiation_id]
        
        message = {
            "action": "negotiation_response",
            "negotiation_id": negotiation_id,
            "status": NegotiationStatus.REJECTED.value,
            "content": {"reason": reason}
        }
        
        return self.comm_manager.send_message(
            self.agent_id, negotiation["initiator"], json.dumps(message))
    
    def counter_offer(self, negotiation_id: str, content: Any) -> bool:
        """
        提出反提议
        
        Args:
            negotiation_id: 协商ID
            content: 反提议内容
            
        Returns:
            bool: 是否成功
        """
        if negotiation_id not in self.negotiations:
            return False
            
        negotiation = self.negotiations[negotiation_id]
        
        message = {
            "action": "negotiation_response",
            "negotiation_id": negotiation_id,
            "status": NegotiationStatus.COUNTEROFFERED.value,
            "content": content
        }
        
        return self.comm_manager.send_message(
            self.agent_id, negotiation["initiator"], json.dumps(message)) 