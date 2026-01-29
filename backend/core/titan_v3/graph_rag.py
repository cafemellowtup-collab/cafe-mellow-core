"""
TITAN v3 SQL-GraphRAG
=====================
Deep reasoning using BigQuery Recursive CTEs instead of expensive Graph Databases.

Features:
1. Relationship tracking between entities (Supplier → Product → Sales)
2. Recursive traversal to find hidden connections
3. Impact analysis across the business graph
4. Cost: Standard SQL query pricing (not Graph DB pricing)
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import hashlib
import os

from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError


class RelationshipType(str, Enum):
    SUPPLIES = "supplies"           # Supplier → Product
    CONTAINS = "contains"           # Product → Ingredient
    SELLS = "sells"                 # Outlet → Product
    EMPLOYS = "employs"             # Outlet → Staff
    MANAGES = "manages"             # Staff → Department
    CAUSES = "causes"               # Event → Event (causal)
    CORRELATES = "correlates"       # Metric → Metric
    DEPENDS_ON = "depends_on"       # Process → Process
    IMPACTS = "impacts"             # Change → Metric
    TRIGGERS = "triggers"           # Condition → Action


class NodeType(str, Enum):
    SUPPLIER = "supplier"
    PRODUCT = "product"
    INGREDIENT = "ingredient"
    OUTLET = "outlet"
    STAFF = "staff"
    DEPARTMENT = "department"
    EVENT = "event"
    METRIC = "metric"
    PROCESS = "process"
    CUSTOMER = "customer"


@dataclass
class GraphNode:
    """A node in the knowledge graph"""
    node_id: str
    node_type: NodeType
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class GraphEdge:
    """An edge (relationship) in the knowledge graph"""
    edge_id: str
    source_id: str
    target_id: str
    relationship: RelationshipType
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TraversalResult:
    """Result of a graph traversal"""
    path: List[GraphNode]
    edges: List[GraphEdge]
    total_weight: float
    depth: int
    impact_score: float


class GraphRAG:
    """
    SQL-based Knowledge Graph with Recursive CTE Traversal
    
    Uses BigQuery's recursive CTEs to simulate graph traversal
    without needing Neo4j or other graph databases.
    """
    
    PROJECT_ID = "cafe-mellow-core-2026"
    DATASET_ID = "cafe_operations"


    def _get_bq_client(project_id: str) -> Tuple[Optional[bigquery.Client], Optional[Exception]]:
        try:
            key_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "service-key.json")
            )
            if os.path.exists(key_path):
                return bigquery.Client.from_service_account_json(key_path), None
            return bigquery.Client(project=project_id), None
        except DefaultCredentialsError as e:
            return None, e
        except Exception as e:
            return None, e


    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id
        self.client, self._bq_init_error = self._get_bq_client(self.PROJECT_ID)
        if self.client:
            self._ensure_tables_exist()


    def _ensure_tables_exist(self):
        """Create graph tables if they don't exist"""

        if not self.client:
            return

        # Nodes table
        nodes_schema = [
            bigquery.SchemaField("node_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("tenant_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("node_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("properties", "JSON"),
            bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
            bigquery.SchemaField("updated_at", "TIMESTAMP"),
        ]

        # Edges table
        edges_schema = [
            bigquery.SchemaField("edge_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("tenant_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("source_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("target_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("relationship", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("weight", "FLOAT64"),
            bigquery.SchemaField("properties", "JSON"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
        ]

        tables = {
            "titan_graph_nodes": nodes_schema,
            "titan_graph_edges": edges_schema,
        }

        for table_name, schema in tables.items():
            table_ref = f"{self.PROJECT_ID}.{self.DATASET_ID}.{table_name}"
            try:
                self.client.get_table(table_ref)
            except Exception:
                table = bigquery.Table(table_ref, schema=schema)
                self.client.create_table(table)


    def add_node(self, node: GraphNode) -> str:
        """Add a node to the graph"""
        if not self.client:
            raise Exception("BigQuery not connected")
        table_ref = f"{self.PROJECT_ID}.{self.DATASET_ID}.titan_graph_nodes"

        row = {
            "node_id": node.node_id,
            "tenant_id": self.tenant_id,
            "node_type": node.node_type.value,
            "name": node.name,
            "properties": node.properties,
            "embedding": node.embedding or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        errors = self.client.insert_rows_json(table_ref, [row])
        if errors:
            raise Exception(f"Failed to insert node: {errors}")

        return node.node_id


    def add_edge(self, edge: GraphEdge) -> str:
        """Add an edge (relationship) to the graph"""
        if not self.client:
            raise Exception("BigQuery not connected")
        table_ref = f"{self.PROJECT_ID}.{self.DATASET_ID}.titan_graph_edges"

        row = {
            "edge_id": edge.edge_id,
            "tenant_id": self.tenant_id,
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "relationship": edge.relationship.value,
            "weight": edge.weight,
            "properties": edge.properties,
            "created_at": datetime.now().isoformat(),
        }

        errors = self.client.insert_rows_json(table_ref, [row])
        if errors:
            raise Exception(f"Failed to insert edge: {errors}")

        return edge.edge_id


    def add_relationship(
        self,
        source_name: str,
        source_type: NodeType,
        target_name: str,
        target_type: NodeType,
        relationship: RelationshipType,
        weight: float = 1.0,
        properties: Optional[Dict] = None
    ) -> Tuple[str, str, str]:
        """Convenience method to add nodes and edge in one call"""

        # Create node IDs
        source_id = hashlib.md5(f"{source_type.value}:{source_name}".encode()).hexdigest()[:16]
        target_id = hashlib.md5(f"{target_type.value}:{target_name}".encode()).hexdigest()[:16]
        edge_id = hashlib.md5(f"{source_id}:{relationship.value}:{target_id}".encode()).hexdigest()[:16]

        # Add nodes (idempotent)
        source_node = GraphNode(
            node_id=source_id,
            node_type=source_type,
            name=source_name,
        )
        target_node = GraphNode(
            node_id=target_id,
            node_type=target_type,
            name=target_name,
        )

        try:
            self.add_node(source_node)
        except:
            pass  # Node might already exist

        try:
            self.add_node(target_node)
        except:
            pass  # Node might already exist

        # Add edge
        edge = GraphEdge(
            edge_id=edge_id,
            source_id=source_id,
            target_id=target_id,
            relationship=relationship,
            weight=weight,
            properties=properties or {},
        )

        try:
            self.add_edge(edge)
        except:
            pass  # Edge might already exist

        return source_id, target_id, edge_id


    def traverse_impact(
        self,
        start_node_name: str,
        max_depth: int = 3,
        relationship_filter: Optional[List[RelationshipType]] = None
    ) -> List[Dict[str, Any]]:
        """
        Traverse the graph to find impact of a node using Recursive CTE

        Example: "What is the impact of Supplier X's delay?"
        """
        if not self.client:
            return [{"error": "BigQuery not connected"}]

        rel_filter = ""
        if relationship_filter:
            rels = ", ".join([f"'{r.value}'" for r in relationship_filter])
            rel_filter = f"AND e.relationship IN ({rels})"

        query = f"""
        WITH RECURSIVE impact_chain AS (
            -- Base case: start node
            SELECT 
                n.node_id,
                n.name,
                n.node_type,
                CAST(1 AS INT64) as depth,
                ARRAY[n.name] as path,
                1.0 as cumulative_weight,
                '' as via_relationship
            FROM `{self.PROJECT_ID}.{self.DATASET_ID}.titan_graph_nodes` n
            WHERE n.tenant_id = '{self.tenant_id}'
                AND LOWER(n.name) LIKE LOWER('%{start_node_name}%')

            UNION ALL

            -- Recursive case: traverse edges
            SELECT 
                n.node_id,
                n.name,
                n.node_type,
                ic.depth + 1,
                ARRAY_CONCAT(ic.path, [n.name]),
                ic.cumulative_weight * e.weight,
                e.relationship
            FROM impact_chain ic
            JOIN `{self.PROJECT_ID}.{self.DATASET_ID}.titan_graph_edges` e
                ON ic.node_id = e.source_id
                AND e.tenant_id = '{self.tenant_id}'
                {rel_filter}
            JOIN `{self.PROJECT_ID}.{self.DATASET_ID}.titan_graph_nodes` n
                ON e.target_id = n.node_id
                AND n.tenant_id = '{self.tenant_id}'
            WHERE ic.depth < {max_depth}
                AND n.name NOT IN UNNEST(ic.path)  -- Prevent cycles
        )
        SELECT 
            node_id,
            name,
            node_type,
            depth,
            path,
            cumulative_weight as impact_score,
            via_relationship
        FROM impact_chain
        WHERE depth > 1
        ORDER BY depth, cumulative_weight DESC
        """

        try:
            results = self.client.query(query).result()
            return [dict(row) for row in results]
        except Exception as e:
            return [{"error": str(e)}]


    def find_connections(
        self,
        node_a_name: str,
        node_b_name: str,
        max_depth: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Find paths connecting two nodes

        Example: "How does Weather affect my Sales?"
        """
        if not self.client:
            return [{"error": "BigQuery not connected"}]

        query = f"""
        WITH RECURSIVE path_finder AS (
            -- Base case: start from node A
            SELECT 
                n.node_id,
                n.name,
                ARRAY[n.name] as path,
                ARRAY<STRING>[] as relationships,
                1 as depth
            FROM `{self.PROJECT_ID}.{self.DATASET_ID}.titan_graph_nodes` n
            WHERE n.tenant_id = '{self.tenant_id}'
                AND LOWER(n.name) LIKE LOWER('%{node_a_name}%')

            UNION ALL

            -- Recursive: follow edges
            SELECT 
                n.node_id,
                n.name,
                ARRAY_CONCAT(pf.path, [n.name]),
                ARRAY_CONCAT(pf.relationships, [e.relationship]),
                pf.depth + 1
            FROM path_finder pf
            JOIN `{self.PROJECT_ID}.{self.DATASET_ID}.titan_graph_edges` e
                ON pf.node_id = e.source_id
                AND e.tenant_id = '{self.tenant_id}'
            JOIN `{self.PROJECT_ID}.{self.DATASET_ID}.titan_graph_nodes` n
                ON e.target_id = n.node_id
            WHERE pf.depth < {max_depth}
                AND n.name NOT IN UNNEST(pf.path)
        )
        SELECT 
            path,
            relationships,
            depth
        FROM path_finder
        WHERE LOWER(name) LIKE LOWER('%{node_b_name}%')
        ORDER BY depth
        LIMIT 5
        """

        try:
            results = self.client.query(query).result()
            return [dict(row) for row in results]
        except Exception as e:
            return [{"error": str(e)}]


    def get_node_neighbors(
        self,
        node_name: str,
        direction: str = "outgoing"  # outgoing, incoming, both
    ) -> List[Dict[str, Any]]:
        """Get immediate neighbors of a node"""
        if not self.client:
            return [{"error": "BigQuery not connected"}]

        if direction == "outgoing":
            join_condition = "e.source_id = n1.node_id AND e.target_id = n2.node_id"
        elif direction == "incoming":
            join_condition = "e.target_id = n1.node_id AND e.source_id = n2.node_id"
        else:
            join_condition = "(e.source_id = n1.node_id AND e.target_id = n2.node_id) OR (e.target_id = n1.node_id AND e.source_id = n2.node_id)"
        
        query = f"""
        SELECT 
            n2.node_id,
            n2.name,
            n2.node_type,
            e.relationship,
            e.weight
        FROM `{self.PROJECT_ID}.{self.DATASET_ID}.titan_graph_nodes` n1
        JOIN `{self.PROJECT_ID}.{self.DATASET_ID}.titan_graph_edges` e
            ON {join_condition}
            AND e.tenant_id = '{self.tenant_id}'
        JOIN `{self.PROJECT_ID}.{self.DATASET_ID}.titan_graph_nodes` n2
            ON n2.tenant_id = '{self.tenant_id}'
        WHERE n1.tenant_id = '{self.tenant_id}'
            AND LOWER(n1.name) LIKE LOWER('%{node_name}%')
        ORDER BY e.weight DESC
        """
        
        try:
            results = self.client.query(query).result()
            return [dict(row) for row in results]
        except Exception as e:
            return [{"error": str(e)}]
    
    def build_context_for_query(self, query: str, max_nodes: int = 10) -> str:
        """
        Build graph context for AI query answering
        
        Extracts relevant subgraph based on query entities
        """
        
        # Extract potential entity names from query
        # Simple extraction - could be enhanced with NER
        words = query.lower().split()
        
        context_parts = []
        
        for word in words:
            if len(word) > 3:  # Skip short words
                neighbors = self.get_node_neighbors(word, "both")
                if neighbors and not neighbors[0].get("error"):
                    for n in neighbors[:3]:
                        context_parts.append(
                            f"- {word} {n.get('relationship', 'relates to')} {n.get('name')}"
                        )
        
        if context_parts:
            return "KNOWLEDGE GRAPH CONTEXT:\n" + "\n".join(context_parts[:max_nodes])
        
        return ""
    
    def auto_learn_relationships(self, event_data: Dict[str, Any]):
        """
        Automatically learn relationships from incoming events
        
        Example: When a sale happens, learn Product → Customer relationship
        """
        
        entity_type = event_data.get("entity_type", "")
        data = event_data.get("data", {})
        
        if entity_type == "order":
            # Learn: Product → Customer, Product → Outlet relationships
            items = data.get("items", [])
            customer = data.get("customer_id", "walk-in")
            outlet = data.get("outlet_id", "main")
            
            for item in items:
                product_name = item.get("name", "Unknown")
                
                self.add_relationship(
                    source_name=product_name,
                    source_type=NodeType.PRODUCT,
                    target_name=customer,
                    target_type=NodeType.CUSTOMER,
                    relationship=RelationshipType.SELLS,
                    weight=item.get("quantity", 1),
                )
        
        elif entity_type == "expense":
            # Learn: Supplier → Product/Ingredient relationships
            vendor = data.get("vendor", "Unknown")
            category = data.get("category", "General")
            items = data.get("items", [])
            
            for item in items:
                self.add_relationship(
                    source_name=vendor,
                    source_type=NodeType.SUPPLIER,
                    target_name=item.get("name", category),
                    target_type=NodeType.INGREDIENT,
                    relationship=RelationshipType.SUPPLIES,
                    weight=item.get("amount", 1),
                )
