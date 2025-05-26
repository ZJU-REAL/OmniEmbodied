from typing import Dict, List, Set, Optional, Any, Tuple, Callable
import logging
import threading
import time
import queue

logger = logging.getLogger(__name__)

class CommunicationManager:
    """
    通信管理器，处理去中心化智能体之间的消息传递
    """
    
    def __init__(self):
        """
        初始化通信管理器
        """
        self.agents: Dict[str, Any] = {}  # 智能体ID到引用的映射
        self.message_queues: Dict[str, queue.Queue] = {}  # 每个智能体的消息队列
        self.message_handlers: Dict[str, Callable] = {}  # 消息处理回调
        self.groups: Dict[str, Set[str]] = {}  # 组ID到成员的映射
        self.agent_groups: Dict[str, Set[str]] = {}  # 智能体ID到所属组的映射
        self.running = False
        self.message_thread = None
    
    def register_agent(self, agent_id: str, agent_ref: Any = None, 
                     message_handler: Optional[Callable] = None) -> None:
        """
        注册智能体
        
        Args:
            agent_id: 智能体ID
            agent_ref: 智能体引用对象
            message_handler: 消息处理回调函数
        """
        if agent_id in self.agents:
            logger.warning(f"智能体 {agent_id} 已注册，将被覆盖")
        
        self.agents[agent_id] = agent_ref
        self.message_queues[agent_id] = queue.Queue()
        
        if message_handler:
            self.message_handlers[agent_id] = message_handler
        
        self.agent_groups[agent_id] = set()
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        注销智能体
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            bool: 是否成功注销
        """
        if agent_id not in self.agents:
            return False
        
        # 从所有组中移除
        for group in self.agent_groups.get(agent_id, set()):
            if group in self.groups:
                self.groups[group].discard(agent_id)
        
        # 清理资源
        del self.agents[agent_id]
        del self.message_queues[agent_id]
        if agent_id in self.message_handlers:
            del self.message_handlers[agent_id]
        if agent_id in self.agent_groups:
            del self.agent_groups[agent_id]
            
        return True
    
    def create_group(self, group_id: str, members: Optional[List[str]] = None) -> bool:
        """
        创建智能体组
        
        Args:
            group_id: 组ID
            members: 成员智能体ID列表
            
        Returns:
            bool: 是否成功创建
        """
        if group_id in self.groups:
            logger.warning(f"组 {group_id} 已存在，将被覆盖")
            
        self.groups[group_id] = set()
        
        if members:
            for agent_id in members:
                self.add_to_group(group_id, agent_id)
                
        return True
    
    def add_to_group(self, group_id: str, agent_id: str) -> bool:
        """
        将智能体添加到组
        
        Args:
            group_id: 组ID
            agent_id: 智能体ID
            
        Returns:
            bool: 是否成功添加
        """
        if group_id not in self.groups:
            self.groups[group_id] = set()
            
        if agent_id not in self.agents:
            return False
            
        self.groups[group_id].add(agent_id)
        
        if agent_id not in self.agent_groups:
            self.agent_groups[agent_id] = set()
            
        self.agent_groups[agent_id].add(group_id)
        return True
    
    def send_message(self, sender_id: str, receiver_id: str, content: Any) -> bool:
        """
        发送消息给特定智能体
        
        Args:
            sender_id: 发送者ID
            receiver_id: 接收者ID
            content: 消息内容
            
        Returns:
            bool: 是否成功发送
        """
        if receiver_id not in self.message_queues:
            logger.warning(f"接收者 {receiver_id} 未注册")
            return False
            
        message = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "content": content,
            "timestamp": time.time(),
            "type": "direct"
        }
        
        self.message_queues[receiver_id].put(message)
        
        # 如果有消息处理器，同步调用
        if receiver_id in self.message_handlers and self.agents.get(receiver_id):
            try:
                handler = self.message_handlers[receiver_id]
                handler(self.agents[receiver_id], sender_id, content)
            except Exception as e:
                logger.exception(f"处理发送到 {receiver_id} 的消息时出错: {e}")
        
        return True
    
    def send_group_message(self, sender_id: str, group_id: str, content: Any) -> int:
        """
        发送消息给组中所有智能体
        
        Args:
            sender_id: 发送者ID
            group_id: 组ID
            content: 消息内容
            
        Returns:
            int: 成功接收消息的智能体数量
        """
        if group_id not in self.groups:
            logger.warning(f"组 {group_id} 不存在")
            return 0
            
        success_count = 0
        
        for receiver_id in self.groups[group_id]:
            if receiver_id != sender_id:  # 不发送给自己
                if self.send_message(sender_id, receiver_id, content):
                    success_count += 1
        
        return success_count
    
    def broadcast_message(self, sender_id: str, content: Any) -> int:
        """
        广播消息给所有已知智能体
        
        Args:
            sender_id: 发送者ID
            content: 消息内容
            
        Returns:
            int: 成功接收消息的智能体数量
        """
        success_count = 0
        
        for receiver_id in self.agents:
            if receiver_id != sender_id:  # 不发送给自己
                if self.send_message(sender_id, receiver_id, content):
                    success_count += 1
        
        return success_count
    
    def start_processing(self) -> None:
        """
        开始处理消息
        """
        if self.running:
            return
            
        self.running = True
        
        # 创建消息处理线程
        self.message_thread = threading.Thread(target=self._message_process_loop)
        self.message_thread.daemon = True  # 设为守护线程，主线程结束时自动结束
        self.message_thread.start()
    
    def stop_processing(self) -> None:
        """
        停止处理消息
        """
        self.running = False
        if self.message_thread:
            self.message_thread.join(timeout=1.0)
    
    def _message_process_loop(self) -> None:
        """
        消息处理循环
        """
        while self.running:
            # 检查所有智能体的消息队列
            for agent_id, msg_queue in self.message_queues.items():
                try:
                    # 非阻塞检查队列
                    if not msg_queue.empty():
                        message = msg_queue.get(block=False)
                        
                        # 如果有消息处理器且智能体引用存在
                        if agent_id in self.message_handlers and self.agents.get(agent_id):
                            try:
                                handler = self.message_handlers[agent_id]
                                sender_id = message.get("sender_id", "unknown")
                                content = message.get("content", "")
                                handler(self.agents[agent_id], sender_id, content)
                            except Exception as e:
                                logger.exception(f"处理发送到 {agent_id} 的消息时出错: {e}")
                        
                        msg_queue.task_done()
                        
                except queue.Empty:
                    pass
                except Exception as e:
                    logger.exception(f"消息处理循环出错: {e}")
            
            # 短暂休眠，避免CPU占用过高
            time.sleep(0.1) 