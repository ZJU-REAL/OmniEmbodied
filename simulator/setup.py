from setuptools import setup, find_packages

# 读取requirements.txt中的依赖
def read_requirements():
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]

# 读取README文件作为长描述
def read_readme():
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Embodied Simulator - 文本具身任务模拟器"

setup(
    name="embodied_simulator",
    version="0.1.0",
    author="Embodied AI Team",
    author_email="",
    description="文本具身任务模拟器",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": ["pytest>=6.0.0", "black", "flake8"],
        "test": ["pytest>=6.0.0"],
    },
    include_package_data=True,
    zip_safe=False,
) 