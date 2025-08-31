

class MongoDBSerializer:
    """处理复杂对象到MongoDB文档的序列化和反序列化"""
    
    @staticmethod
    def serialize(obj: Any) -> Any:
        """将对象序列化为MongoDB可存储的格式"""
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, list):
            return [MongoDBSerializer.serialize(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: MongoDBSerializer.serialize(value) for key, value in obj.items()}
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return MongoDBSerializer.serialize(obj.__dict__)
        else:
            return str(obj)
    
    @staticmethod
    def deserialize(data: Any, target_class: Optional[type] = None):
        """将MongoDB文档反序列化为对象"""
        if isinstance(data, (str, int, float, bool, type(None))):
            return data
        elif isinstance(data, list):
            return [MongoDBSerializer.deserialize(item) for item in data]
        elif isinstance(data, dict):
            # 如果有目标类并且有from_dict方法，使用它
            if target_class and hasattr(target_class, 'from_dict'):
                return target_class.from_dict(data)
            
            # 处理可能包含_type字段的嵌套对象
            if '_type' in data and data['_type'] == 'User':
                return User.from_dict(data)
                
            # 普通字典
            return {key: MongoDBSerializer.deserialize(value) for key, value in data.items()}
        else:
            return data
            
            
class MongoDBManager:
    """管理MongoDB连接和操作"""
    
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", db_name: str = "my_app"):
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.serializer = MongoDBSerializer()
    
    def save_c1(self, c1_instance: C1) -> str:
        """保存C1实例到MongoDB"""
        collection = self.db['c1_collection']
        
        # 序列化对象
        data = self.serializer.serialize(c1_instance)
        data['_type'] = 'C1'  # 添加类型标识
        
        # 添加或更新时间戳
        now = datetime.now().isoformat()
        if '_id' in data:
            data['updated_at'] = now
            result = collection.update_one({'_id': data['_id']}, {'$set': data})
            return str(data['_id'])
        else:
            data['created_at'] = now
            data['updated_at'] = now
            result = collection.insert_one(data)
            return str(result.inserted_id)
    
    def save_c2(self, c2_instance: C2) -> str:
        """保存C2实例到MongoDB"""
        collection = self.db['c2_collection']
        
        # 序列化对象
        data = self.serializer.serialize(c2_instance)
        data['_type'] = 'C2'  # 添加类型标识
        
        # 添加或更新时间戳
        now = datetime.now().isoformat()
        if hasattr(c2_instance, '_id') and c2_instance._id:
            data['_id'] = c2_instance._id
            data['updated_at'] = now
            result = collection.update_one({'_id': data['_id']}, {'$set': data})
            return str(data['_id'])
        else:
            data['created_at'] = now
            data['updated_at'] = now
            result = collection.insert_one(data)
            # 保存ID回对象，便于后续更新
            c2_instance._id = result.inserted_id
            return str(result.inserted_id)
    
    def load_c1(self, cid: str) -> Optional[C1]:
        """根据CID加载C1实例"""
        collection = self.db['c1_collection']
        document = collection.find_one({'cid': cid})
        
        if not document:
            return None
        
        # 移除MongoDB的_id字段，避免干扰反序列化
        document.pop('_id', None)
        
        # 反序列化
        c1_instance = C1(
            cid=document['cid'],
            users=[User.from_dict(user_data) for user_data in document.get('users', [])],
            metadata=document.get('metadata', {})
        )
        
        # 设置时间字段
        if 'created_at' in document:
            c1_instance.created_at = datetime.fromisoformat(document['created_at'])
        if 'updated_at' in document:
            c1_instance.updated_at = datetime.fromisoformat(document['updated_at'])
            
        return c1_instance
    
    def load_c2(self, cid: str) -> Optional[C2]:
        """根据CID加载C2实例"""
        collection = self.db['c2_collection']
        document = collection.find_one({'cid': cid})
        
        if not document:
            return None
        
        # 创建C2实例
        c2_instance = C2()
        c2_instance.cid = document['cid']
        c2_instance.users = [User.from_dict(user_data) for user_data in document.get('users', [])]
        c2_instance.tags = document.get('tags', [])
        
        # 设置时间字段
        if 'created_at' in document:
            c2_instance.created_at = datetime.fromisoformat(document['created_at'])
        if 'updated_at' in document:
            c2_instance.updated_at = datetime.fromisoformat(document['updated_at'])
            
        # 保存MongoDB的_id用于后续更新
        c2_instance._id = document['_id']
            
        return c2_instance
    
    def query_c1_by_user_email(self, email: str) -> List[C1]:
        """查询包含特定邮箱用户的C1实例"""
        collection = self.db['c1_collection']
        
        # 使用MongoDB的数组查询操作符
        results = collection.find({'users.email': email})
        
        c1_instances = []
        for document in results:
            # 移除MongoDB的_id字段
            document.pop('_id', None)
            
            # 反序列化
            c1_instance = C1(
                cid=document['cid'],
                users=[User.from_dict(user_data) for user_data in document.get('users', [])],
                metadata=document.get('metadata', {})
            )
            
            # 设置时间字段
            if 'created_at' in document:
                c1_instance.created_at = datetime.fromisoformat(document['created_at'])
            if 'updated_at' in document:
                c1_instance.updated_at = datetime.fromisoformat(document['updated_at'])
                
            c1_instances.append(c1_instance)
            
        return c1_instances
    
    def query_c2_by_tag(self, tag: str) -> List[C2]:
        """查询包含特定标签的C2实例"""
        collection = self.db['c2_collection']
        
        # 使用MongoDB的数组查询操作符
        results = collection.find({'tags': tag})
        
        c2_instances = []
        for document in results:
            # 创建C2实例
            c2_instance = C2()
            c2_instance.cid = document['cid']
            c2_instance.users = [User.from_dict(user_data) for user_data in document.get('users', [])]
            c2_instance.tags = document.get('tags', [])
            
            # 设置时间字段
            if 'created_at' in document:
                c2_instance.created_at = datetime.fromisoformat(document['created_at'])
            if 'updated_at' in document:
                c2_instance.updated_at = datetime.fromisoformat(document['updated_at'])
                
            # 保存MongoDB的_id用于后续更新
            c2_instance._id = document['_id']
                
            c2_instances.append(c2_instance)
            
        return c2_instances
    
    def create_indexes(self):
        """创建常用查询的索引以提高性能"""
        # 为C1集合创建索引
        self.db['c1_collection'].create_index([('cid', ASCENDING)], unique=True)
        self.db['c1_collection'].create_index([('users.email', ASCENDING)])
        self.db['c1_collection'].create_index([('created_at', DESCENDING)])
        
        # 为C2集合创建索引
        self.db['c2_collection'].create_index([('cid', ASCENDING)], unique=True)
        self.db['c2_collection'].create_index([('tags', ASCENDING)])
        self.db['c2_collection'].create_index([('created_at', DESCENDING)])
    
    def close_connection(self):
        """关闭数据库连接"""
        self.client.close()