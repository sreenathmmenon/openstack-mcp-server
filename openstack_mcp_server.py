#!/usr/bin/env python3
"""
OpenStack MCP Server

A comprehensive MCP server for OpenStack infrastructure management.
Compatible with MCP CLI, MCP Gateway, and other MCP client applications.

Author: Sreenath
Email: zreenathmenon@gmail.com
Repository: https://github.com/sreenathmmenon/openstack-mcp-server
"""

import asyncio
import json
import os
import sys
from typing import Dict, List, Optional, Any

# MCP imports
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
import mcp.server.stdio
import mcp.types as types

# OpenStack Client
from openstack_client import OpenStackClient

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OpenStackMCPServer:
    """OpenStack MCP Server implementation for MCP 1.12.2"""
    
    def __init__(self):
        self.server = Server("openstack-mcp-server")
        self.openstack_client = OpenStackClient()
        
        # Register all MCP tools and handlers
        self._register_tools()
        self._register_handlers()
    
    def _register_tools(self):
        """Register all MCP tool definitions"""
        
        @self.server.list_tools()
        async def handle_list_tools():
            return [
                # ============ COMPUTE ============
                types.Tool(
                    name="list_servers",
                    description="List all virtual machines/servers in the OpenStack environment with their current status, IDs, and basic configuration",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                types.Tool(
                    name="get_server_details",
                    description="Get detailed information about a specific virtual machine/server including status, host, resources, and configuration",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "server_id": {
                                "type": "string",
                                "description": "Unique identifier of the virtual machine/server (UUID)"
                            }
                        },
                        "required": ["server_id"]
                    }
                ),
                types.Tool(
                    name="list_hypervisors",
                    description="List all hypervisor hosts in OpenStack with their resource usage, capacity, and status details",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                types.Tool(
                    name="list_flavors",
                    description="List all compute flavors/templates available in OpenStack with their resource specifications",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                types.Tool(
                    name="get_flavor_details",
                    description="Get detailed information about a specific compute flavor/template including resource specs and extra specifications",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "flavor_id": {
                                "type": "string",
                                "description": "Unique identifier of the compute flavor (UUID)"
                            }
                        },
                        "required": ["flavor_id"]
                    }
                ),
                
                # ============ GLANCE/IMAGE ============
                types.Tool(
                    name="list_images",
                    description="List all virtual machine images available in OpenStack with their status and properties",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                types.Tool(
                    name="get_image_details",
                    description="Get detailed information about a specific virtual machine image including metadata and properties",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "image_id": {
                                "type": "string",
                                "description": "Unique identifier of the virtual machine image (UUID)"
                            }
                        },
                        "required": ["image_id"]
                    }
                ),
                
                # ============ STORAGE ============
                types.Tool(
                    name="list_volumes",
                    description="List all storage volumes in OpenStack with their status, size, and attachment information",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                types.Tool(
                    name="list_volume_types",
                    description="List all volume types available in OpenStack with their specifications and extra specs",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                
                # ============ NETWORK ============
                types.Tool(
                    name="list_networks",
                    description="List all networks in OpenStack with their status, type, and configuration details",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                types.Tool(
                    name="list_subnets",
                    description="List all subnets in OpenStack with their CIDR, gateway, and DHCP configuration",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                types.Tool(
                    name="list_routers",
                    description="List all routers in OpenStack with their status and gateway configuration",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                
                # ============ ANALYSIS ============
                types.Tool(
                    name="analyze_server_resources",
                    description="Analyze server resource allocation, hypervisor placement, and health status for troubleshooting and optimization",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "server_id": {
                                "type": "string",
                                "description": "Unique identifier of the virtual machine/server (UUID)"
                            }
                        },
                        "required": ["server_id"]
                    }
                ),
                types.Tool(
                    name="get_infrastructure_summary",
                    description="Get a comprehensive summary of the OpenStack infrastructure including resource utilization and health status",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                
                # ============ MONITORING ============
                types.Tool(
                    name="get_resource_utilization",
                    description="Get current resource utilization across all hypervisors including CPU, memory, and storage usage",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                types.Tool(
                    name="check_service_health",
                    description="Check the health status of OpenStack services and identify any issues or errors",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                
                # ============ INVENTORY/REPORTING ============
                types.Tool(
                    name="generate_inventory_report",
                    description="Generate a comprehensive inventory report of all OpenStack resources including compute, storage, networking, utilization metrics, and optimization recommendations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "format": {
                                "type": "string",
                                "description": "Report format: 'summary' for high-level overview or 'detailed' for complete resource listings",
                                "enum": ["summary", "detailed"],
                                "default": "detailed"
                            }
                        },
                        "required": []
                    }
                )
            ]
    
    def _register_handlers(self):
        """Register all MCP tool handlers"""
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
            try:
                result = await self._execute_tool(name, arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                error_msg = f"Error executing tool '{name}': {str(e)}"
                return [types.TextContent(type="text", text=error_msg)]
    
    async def _execute_tool(self, name: str, arguments: dict) -> Any:
        """Execute the specified tool with given arguments"""
        
        if name == "list_servers":
            return self.openstack_client.list_servers()
        
        elif name == "get_server_details":
            server_id = arguments.get("server_id")
            if not server_id:
                raise ValueError("server_id is required")
            return self.openstack_client.get_server_details(server_id)
        
        elif name == "list_hypervisors":
            return self.openstack_client.list_hypervisors()
        
        elif name == "list_flavors":
            return self.openstack_client.list_flavors()
        
        elif name == "get_flavor_details":
            flavor_id = arguments.get("flavor_id")
            if not flavor_id:
                raise ValueError("flavor_id is required")
            return self.openstack_client.get_flavor_details(flavor_id)
        
        elif name == "list_images":
            return self.openstack_client.list_images()
        
        elif name == "get_image_details":
            image_id = arguments.get("image_id")
            if not image_id:
                raise ValueError("image_id is required")
            return self.openstack_client.get_image_details(image_id)
        
        elif name == "list_volumes":
            return self.openstack_client.list_volumes()
        
        elif name == "list_volume_types":
            return self.openstack_client.list_volume_types()
        
        elif name == "list_networks":
            return self.openstack_client.list_networks()
        
        elif name == "list_subnets":
            return self.openstack_client.list_subnets()
        
        elif name == "list_routers":
            return self.openstack_client.list_routers()
        
        elif name == "analyze_server_resources":
            server_id = arguments.get("server_id")
            if not server_id:
                raise ValueError("server_id is required")
            return self.openstack_client.analyze_server_resources(server_id)
        
        elif name == "get_infrastructure_summary":
            return await self._get_infrastructure_summary()
        
        elif name == "get_resource_utilization":
            return await self._get_resource_utilization()
        
        elif name == "check_service_health":
            return await self._check_service_health()
        
        elif name == "generate_inventory_report":
            report_format = arguments.get("format", "detailed")
            return self.openstack_client.generate_inventory_report(report_format)
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def _get_infrastructure_summary(self) -> Dict[str, Any]:
        """Get comprehensive infrastructure summary"""
        try:
            # Get all infrastructure data
            servers = self.openstack_client.list_servers()
            hypervisors = self.openstack_client.list_hypervisors()
            volumes = self.openstack_client.list_volumes()
            networks = self.openstack_client.list_networks()
            
            # Calculate summaries
            server_states = {}
            for server in servers:
                state = server.get('status', 'unknown')
                server_states[state] = server_states.get(state, 0) + 1
            
            # Hypervisor capacity
            total_vcpus = sum(h.get('vcpus', 0) for h in hypervisors)
            used_vcpus = sum(h.get('vcpus_used', 0) for h in hypervisors)
            total_memory = sum(h.get('memory_mb', 0) for h in hypervisors)
            used_memory = sum(h.get('memory_mb_used', 0) for h in hypervisors)
            
            return {
                "timestamp": "current",
                "compute": {
                    "servers": {
                        "total": len(servers),
                        "by_status": server_states
                    },
                    "hypervisors": {
                        "total": len(hypervisors),
                        "vcpus": {
                            "total": total_vcpus,
                            "used": used_vcpus,
                            "available": total_vcpus - used_vcpus,
                            "utilization_percent": round((used_vcpus / total_vcpus * 100), 2) if total_vcpus > 0 else 0
                        },
                        "memory": {
                            "total_mb": total_memory,
                            "used_mb": used_memory,
                            "available_mb": total_memory - used_memory,
                            "utilization_percent": round((used_memory / total_memory * 100), 2) if total_memory > 0 else 0
                        }
                    }
                },
                "storage": {
                    "volumes": {
                        "total": len(volumes),
                        "total_size_gb": sum(v.get('size', 0) for v in volumes)
                    }
                },
                "network": {
                    "networks": {
                        "total": len(networks),
                        "external": len([n for n in networks if n.get('external')])
                    }
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to get infrastructure summary: {str(e)}"}
    
    async def _get_resource_utilization(self) -> Dict[str, Any]:
        """Get detailed resource utilization"""
        try:
            hypervisors = self.openstack_client.list_hypervisors()
            
            utilization_data = []
            for hypervisor in hypervisors:
                vcpus_total = hypervisor.get('vcpus', 0)
                vcpus_used = hypervisor.get('vcpus_used', 0)
                memory_total = hypervisor.get('memory_mb', 0)
                memory_used = hypervisor.get('memory_mb_used', 0)
                disk_total = hypervisor.get('local_gb', 0)
                disk_used = hypervisor.get('local_gb_used', 0)
                
                utilization_data.append({
                    "hypervisor": hypervisor.get('hypervisor_hostname'),
                    "status": hypervisor.get('status'),
                    "running_vms": hypervisor.get('running_vms', 0),
                    "cpu": {
                        "total": vcpus_total,
                        "used": vcpus_used,
                        "utilization_percent": round((vcpus_used / vcpus_total * 100), 2) if vcpus_total > 0 else 0
                    },
                    "memory": {
                        "total_mb": memory_total,
                        "used_mb": memory_used,
                        "utilization_percent": round((memory_used / memory_total * 100), 2) if memory_total > 0 else 0
                    },
                    "disk": {
                        "total_gb": disk_total,
                        "used_gb": disk_used,
                        "utilization_percent": round((disk_used / disk_total * 100), 2) if disk_total > 0 else 0
                    }
                })
            
            return {
                "timestamp": "current",
                "hypervisors": utilization_data,
                "summary": {
                    "total_hypervisors": len(hypervisors),
                    "active_hypervisors": len([h for h in hypervisors if h.get('status') == 'enabled']),
                    "total_vms": sum(h.get('running_vms', 0) for h in hypervisors)
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to get resource utilization: {str(e)}"}
    
    async def _check_service_health(self) -> Dict[str, Any]:
        """Check OpenStack service health"""
        try:
            # Check basic connectivity to services
            health_status = {
                "timestamp": "current",
                "services": {},
                "overall_status": "healthy"
            }
            
            # Test Nova service
            try:
                servers = self.openstack_client.list_servers()
                health_status["services"]["nova"] = {
                    "status": "healthy",
                    "message": f"Successfully retrieved {len(servers)} servers",
                    "last_check": "current"
                }
            except Exception as e:
                health_status["services"]["nova"] = {
                    "status": "unhealthy",
                    "message": f"Nova service error: {str(e)}",
                    "last_check": "current"
                }
                health_status["overall_status"] = "degraded"
            
            # Test Cinder service
            try:
                volumes = self.openstack_client.list_volumes()
                health_status["services"]["cinder"] = {
                    "status": "healthy",
                    "message": f"Successfully retrieved {len(volumes)} volumes",
                    "last_check": "current"
                }
            except Exception as e:
                health_status["services"]["cinder"] = {
                    "status": "unhealthy",
                    "message": f"Cinder service error: {str(e)}",
                    "last_check": "current"
                }
                health_status["overall_status"] = "degraded"
            
            # Test Neutron service
            try:
                networks = self.openstack_client.list_networks()
                health_status["services"]["neutron"] = {
                    "status": "healthy",
                    "message": f"Successfully retrieved {len(networks)} networks",
                    "last_check": "current"
                }
            except Exception as e:
                health_status["services"]["neutron"] = {
                    "status": "unhealthy",
                    "message": f"Neutron service error: {str(e)}",
                    "last_check": "current"
                }
                health_status["overall_status"] = "degraded"
            
            # Check critical issues
            unhealthy_services = [svc for svc, data in health_status["services"].items() 
                                if data["status"] == "unhealthy"]
            
            if len(unhealthy_services) >= 2:
                health_status["overall_status"] = "critical"
            elif len(unhealthy_services) == 1:
                health_status["overall_status"] = "degraded"
            
            health_status["summary"] = {
                "healthy_services": len([s for s in health_status["services"].values() if s["status"] == "healthy"]),
                "unhealthy_services": len(unhealthy_services),
                "total_services": len(health_status["services"])
            }
            
            return health_status
            
        except Exception as e:
            return {
                "timestamp": "current",
                "overall_status": "critical",
                "error": f"Failed to check service health: {str(e)}"
            }
    
    async def run(self):
        """Run the MCP server"""
        try:
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="openstack-mcp-server",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={}
                        )
                    )
                )
        except Exception as e:
            print(f"Server error: {e}")
            import traceback
            traceback.print_exc()
            raise

def main():
    """Main entry point for command line execution"""
    asyncio.run(async_main())

async def async_main():
    """Async main entry point"""
    print("Starting OpenStack MCP Server...")
    
    try:
        server = OpenStackMCPServer()
        print(f"OpenStack MCP Server initialized")
        print(f"Available tools: 17 comprehensive OpenStack management tools")
        print(f"Configuration: Environment variables or config/openstack_config.json")
        print(f"Ready for MCP CLI, MCP Gateway, and other MCP client applications")
        print(f"Waiting for MCP client connections...")
        
        await server.run()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
