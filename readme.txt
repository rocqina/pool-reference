#安装kafka包,安装的是kafka-python，不是kafka。kafka是老得包
,#安装mysql包
执行pip3 install -r requirements.txt



pip3 install pymysql
pip3 install dbutils
pip3 install protobuf
pip3 install kafka-python
pip3 install redis


protoc --python_out=./proto/ chia.proto
