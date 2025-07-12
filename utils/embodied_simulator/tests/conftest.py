import sys
import os
from pathlib import Path
 
# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root)) 