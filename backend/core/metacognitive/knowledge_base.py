"""
System Knowledge Base
Auto-generated documentation and system intelligence
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class KnowledgeType(str, Enum):
    """Knowledge Entry Types"""
    USER_MANUAL = "user_manual"
    API_DOCS = "api_docs"
    BUSINESS_RULE = "business_rule"
    TROUBLESHOOTING = "troubleshooting"
    RELEASE_NOTE = "release_note"
    PATTERN = "pattern"


class KnowledgeEntry(BaseModel):
    """System Knowledge Entry"""
    id: str
    type: KnowledgeType
    title: str
    content: str
    
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    
    related_entries: List[str] = Field(default_factory=list)
    
    version: str = "1.0"
    language: str = "en"
    
    auto_generated: bool = False
    verified: bool = False
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SystemKnowledgeBase:
    """
    System Knowledge Base Manager
    Stores and retrieves system documentation
    """
    
    def __init__(self, client, settings):
        self.client = client
        self.settings = settings
        self.table_name = "system_knowledge_base"
    
    def create_entry(self, entry: KnowledgeEntry) -> bool:
        """Create a new knowledge entry"""
        try:
            table_id = f"{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.{self.table_name}"
            rows = [entry.dict()]
            errors = self.client.insert_rows_json(table_id, rows)
            return not errors
        except Exception:
            return False
    
    def search(self, query: str, type: Optional[KnowledgeType] = None, limit: int = 10) -> List[KnowledgeEntry]:
        """Search knowledge base"""
        try:
            where_conditions = [f"LOWER(content) LIKE LOWER('%{query}%') OR LOWER(title) LIKE LOWER('%{query}%')"]
            
            if type:
                where_conditions.append(f"type = '{type.value}'")
            
            where_clause = " AND ".join(where_conditions)
            
            sql = f"""
            SELECT *
            FROM `{self.settings.PROJECT_ID}.{self.settings.DATASET_ID}.{self.table_name}`
            WHERE {where_clause}
            ORDER BY updated_at DESC
            LIMIT {limit}
            """
            
            result = self.client.query(sql).result()
            
            entries = []
            for row in result:
                entries.append(KnowledgeEntry(**dict(row)))
            
            return entries
        except Exception:
            return []
    
    def auto_generate_api_docs(self, router_name: str, endpoints: List[Dict[str, Any]]) -> KnowledgeEntry:
        """Auto-generate API documentation from router"""
        import uuid
        
        content = f"# {router_name} API Documentation\n\n"
        
        for endpoint in endpoints:
            content += f"## {endpoint['method']} {endpoint['path']}\n\n"
            content += f"{endpoint.get('description', 'No description')}\n\n"
            
            if endpoint.get('parameters'):
                content += "### Parameters\n\n"
                for param in endpoint['parameters']:
                    content += f"- `{param['name']}` ({param['type']}): {param.get('description', '')}\n"
                content += "\n"
        
        return KnowledgeEntry(
            id=str(uuid.uuid4()),
            type=KnowledgeType.API_DOCS,
            title=f"{router_name} API Documentation",
            content=content,
            tags=["api", "auto-generated", router_name],
            auto_generated=True,
            verified=False
        )
