"""
OpenStack Client

Python client for OpenStack API operations (Nova, Cinder, Neutron, Keystone).
Supports authentication, resource management, and comprehensive reporting.

Author: Sreenath
Email: zreenathmenon@gmail.com
Repository: https://github.com/sreenathmmenon/openstack-mcp-server
"""

import requests
import json
import urllib3
from urllib.parse import urlparse 
import os
from typing import Dict, List, Optional, Any

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OpenStackClient:
    """OpenStack API client for Nova, Cinder, Neutron services"""
    
    def __init__(self):
        self.config = self._load_config()
        self.token = None
        self.project_id = None
        
        # Parse base URL from auth URL
        parsed_auth_url = urlparse(self.config['AUTH_URL'])
        self.base_url = f"{parsed_auth_url.scheme}://{parsed_auth_url.netloc}"
        
        # Service URLs
        self.service_urls = {
            'nova': f"{self.base_url}/compute/v2.1",
            'cinder': f"{self.base_url}/volume/v3", 
            'neutron': f"{self.base_url}/networking/v2.0",
            'keystone': self.config['AUTH_URL']
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load OpenStack configuration from environment variables or config file"""
        
        # Priority 1: Environment variables (if present)
        if os.getenv('OS_AUTH_URL'):
            print("Using environment variables for OpenStack configuration")
            return {
                'AUTH_URL': os.getenv('OS_AUTH_URL'),
                'USERNAME': os.getenv('OS_USERNAME'),
                'PASSWORD': os.getenv('OS_PASSWORD'),
                'PROJECT': os.getenv('OS_PROJECT_NAME'),
                'DOMAIN': os.getenv('OS_USER_DOMAIN_NAME', 'Default'),
                'REGION': os.getenv('OS_REGION_NAME', 'RegionOne')
            }
        
        # Priority 2: Default config file
        config_file = os.path.join(os.path.dirname(__file__), "config", "openstack_config.json")
        if os.path.exists(config_file):
            print(f"Loading config from: {config_file}")
            with open(config_file, 'r') as f:
                return json.load(f)
        
        # Fallback: Error if nothing found
        raise FileNotFoundError("No OpenStack configuration found. Set environment variables or create config/openstack_config.json")
    
    def get_token(self) -> str:
        """Get Keystone authentication token"""
        if self.token:
            return self.token
        
        auth_data = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "name": self.config["USERNAME"],
                            "domain": {"name": self.config["DOMAIN"]},
                            "password": self.config["PASSWORD"]
                        }
                    }
                },
                "scope": {
                    "project": {
                        "name": self.config["PROJECT"],
                        "domain": {"name": self.config["DOMAIN"]}
                    }
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.config['AUTH_URL']}/auth/tokens",
                json=auth_data,
                verify=False,
                timeout=30
            )
            response.raise_for_status()
            
            self.token = response.headers['X-Subject-Token']
            self.project_id = response.json()['token']['project']['id']
            return self.token
            
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authenticated headers"""
        return {"X-Auth-Token": self.get_token()}
    
    def _api_call(self, endpoint: str, service: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """Make authenticated API call"""
        if service not in self.service_urls:
            raise ValueError(f"Unknown service: {service}")
        
        # Construct URL with project_id for services that need it
        if service in ['nova', 'cinder'] and self.project_id:
            url = f"{self.service_urls[service]}/{self.project_id}{endpoint}"
        else:
            url = f"{self.service_urls[service]}{endpoint}"
        
        try:
            response = requests.request(
                method, url, 
                headers=self._get_headers(), 
                verify=False, 
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API call failed for {service}{endpoint}: {str(e)}")
    

    # ============ COMPUTE/NOVAOPERATIONS ============
    
    def list_servers(self) -> List[Dict]:
        """List all virtual machines/servers"""
        try:
            servers_data = self._api_call('/servers/detail', 'nova')
            servers = servers_data.get('servers', [])
            
            return [{
                'id': server.get('id'),
                'name': server.get('name'),
                'status': server.get('status'),
                'state': server.get('status'),  # Alias for compatibility
                'host': server.get('OS-EXT-SRV-ATTR:host'),
                'created': server.get('created'),
                'flavor': server.get('flavor', {}).get('id'),
                'image': server.get('image', {}).get('id') if server.get('image') else None,
                'power_state': server.get('OS-EXT-STS:power_state'),
                'task_state': server.get('OS-EXT-STS:task_state')
            } for server in servers]
            
        except Exception as e:
            print(f"Error listing servers: {e}")
            return []
    
    
    def get_server_details(self, server_id: str) -> Optional[Dict]:
        """Get detailed information about a specific server(virtual machine)"""
        try:
            server_data = self._api_call(f"/servers/{server_id}", 'nova')
            server = server_data.get("server", {})
            
            return {
                "id": server.get("id"),
                "name": server.get("name"),
                "status": server.get("status"),
                "host": server.get("OS-EXT-SRV-ATTR:host"),
                "flavor": server.get("flavor", {}).get("id"),
                "image": server.get("image", {}).get("id") if server.get("image") else None,
                "fault": server.get("fault"),
                "power_state": server.get("OS-EXT-STS:power_state"),
                "task_state": server.get("OS-EXT-STS:task_state"),
                "created": server.get("created"),
                "updated": server.get("updated"),
                "addresses": server.get("addresses", {}),
                "metadata": server.get("metadata", {})
            }
            
        except Exception as e:
            print(f"Error getting server details: {e}")
            return None
    
    def list_hypervisors(self) -> List[Dict]:
        """List all available hypervisor hosts"""
        try:
            hypervisors_data = self._api_call("/os-hypervisors/detail", 'nova')
            hypervisors = hypervisors_data.get('hypervisors', [])
            
            return [{
                'id': hypervisor.get('id'),
                'name': hypervisor.get('hypervisor_hostname'),
                'hypervisor_hostname': hypervisor.get('hypervisor_hostname'),
                'state': hypervisor.get('state'),
                'status': hypervisor.get('status'),
                'vcpus': hypervisor.get('vcpus'),
                'vcpus_used': hypervisor.get('vcpus_used'),
                'memory_mb': hypervisor.get('memory_mb'),
                'memory_mb_used': hypervisor.get('memory_mb_used'),
                'local_gb': hypervisor.get('local_gb'),
                'local_gb_used': hypervisor.get('local_gb_used'),
                'free_ram_mb': hypervisor.get('free_ram_mb'),
                'free_disk_gb': hypervisor.get('free_disk_gb'),
                'running_vms': hypervisor.get('running_vms'),
                'hypervisor_type': hypervisor.get('hypervisor_type'),
                'hypervisor_version': hypervisor.get('hypervisor_version')
            } for hypervisor in hypervisors]
            
        except Exception as e:
            print(f"Error listing hypervisors: {e}")
            return []
    
    def list_flavors(self) -> List[Dict]:
        """List all flavors/compute templates"""
        try:
            flavors_data = self._api_call('/flavors/detail', 'nova')
            flavors = flavors_data.get('flavors', [])
            
            return [{
                'id': flavor.get('id'),
                'name': flavor.get('name'),
                'vcpus': flavor.get('vcpus'),
                'ram': flavor.get('ram'),
                'disk': flavor.get('disk'),
                'ephemeral': flavor.get('OS-FLV-EXT-DATA:ephemeral'),
                'swap': flavor.get('swap', 0),
                'is_public': flavor.get('os-flavor-access:is_public')
            } for flavor in flavors]
            
        except Exception as e:
            print(f"Error listing flavors: {e}")
            return []
    
    def get_flavor_details(self, flavor_id: str) -> Optional[Dict]:
        """Get detailed information for a specific flavor"""
        try:
            flavor_data = self._api_call(f"/flavors/{flavor_id}", 'nova')
            flavor = flavor_data.get("flavor", {})
            
            return {
                'id': flavor.get('id'),
                'name': flavor.get('name'),
                'vcpus': flavor.get('vcpus'),
                'ram': flavor.get('ram'),
                'disk': flavor.get('disk'),
                'ephemeral': flavor.get('OS-FLV-EXT-DATA:ephemeral'),
                'swap': flavor.get('swap', 0),
                'is_public': flavor.get('os-flavor-access:is_public'),
                'extra_specs': flavor.get('OS-FLV-WITH-EXT-SPECS:extra_specs', {})
            }
            
        except Exception as e:
            print(f"Error getting flavor details: {e}")
            return None

    # ============ IMAGE OPERATIONS ============
    
    def list_images(self) -> List[Dict]:
        """List all images"""
        try:
            images_data = self._api_call('/images/detail', 'nova')
            images = images_data.get('images', [])
            
            return [{
                'id': image.get('id'),
                'name': image.get('name'),
                'status': image.get('status'),
                'created': image.get('created'),
                'updated': image.get('updated'),
                'size': image.get('size'),
                'min_disk': image.get('minDisk'),
                'min_ram': image.get('minRam'),
                'progress': image.get('progress')
            } for image in images]
            
        except Exception as e:
            print(f"Error listing images: {e}")
            return []
    
    def get_image_details(self, image_id: str) -> Optional[Dict]:
        """Get detailed information about a specific image"""
        try:
            image_data = self._api_call(f"/images/{image_id}", 'nova')
            image = image_data.get("image", {})
            
            return {
                'id': image.get('id'),
                'name': image.get('name'),
                'status': image.get('status'),
                'created': image.get('created'),
                'updated': image.get('updated'),
                'size': image.get('size'),
                'min_disk': image.get('minDisk'),
                'min_ram': image.get('minRam'),
                'progress': image.get('progress'),
                'metadata': image.get('metadata', {})
            }
            
        except Exception as e:
            print(f"Error getting image details: {e}")
            return None

    # ============ STORAGE (CINDER) OPERATIONS ============
    
    def list_volumes(self) -> List[Dict]:
        """List all volumes"""
        try:
            volumes_data = self._api_call('/volumes/detail', 'cinder')
            volumes = volumes_data.get('volumes', [])
            
            return [{
                'id': volume.get('id'),
                'name': volume.get('name'),
                'status': volume.get('status'),
                'size': volume.get('size'),
                'volume_type': volume.get('volume_type'),
                'created_at': volume.get('created_at'),
                'attachments': volume.get('attachments', []),
                'availability_zone': volume.get('availability_zone')
            } for volume in volumes]
            
        except Exception as e:
            print(f"Error listing volumes: {e}")
            return []
    
    def list_volume_types(self) -> List[Dict]:
        """List all volume types/storage templates"""
        try:
            types_data = self._api_call('/types', 'cinder')
            volume_types = types_data.get('volume_types', [])
            
            return [{
                'id': vtype.get('id'),
                'name': vtype.get('name'),
                'description': vtype.get('description'),
                'is_public': vtype.get('is_public'),
                'extra_specs': vtype.get('extra_specs', {})
            } for vtype in volume_types]
            
        except Exception as e:
            print(f"Error listing volume types: {e}")
            return []

    # ============ NETWORK (NEUTRON) OPERATIONS ============
    
    def list_networks(self) -> List[Dict]:
        """List all networks"""
        try:
            networks_data = self._api_call('/networks', 'neutron')
            networks = networks_data.get('networks', [])
            
            return [{
                'id': network.get('id'),
                'name': network.get('name'),
                'status': network.get('status'),
                'admin_state_up': network.get('admin_state_up'),
                'shared': network.get('shared'),
                'external': network.get('router:external'),
                'provider_network_type': network.get('provider:network_type'),
                'subnets': network.get('subnets', [])
            } for network in networks]
            
        except Exception as e:
            print(f"Error listing networks: {e}")
            return []
    
    def list_subnets(self) -> List[Dict]:
        """List all subnets"""
        try:
            subnets_data = self._api_call('/subnets', 'neutron')
            subnets = subnets_data.get('subnets', [])
            
            return [{
                'id': subnet.get('id'),
                'name': subnet.get('name'),
                'network_id': subnet.get('network_id'),
                'cidr': subnet.get('cidr'),
                'ip_version': subnet.get('ip_version'),
                'gateway_ip': subnet.get('gateway_ip'),
                'enable_dhcp': subnet.get('enable_dhcp'),
                'allocation_pools': subnet.get('allocation_pools', [])
            } for subnet in subnets]
            
        except Exception as e:
            print(f"Error listing subnets: {e}")
            return []
    
    def list_routers(self) -> List[Dict]:
        """List all routers"""
        try:
            routers_data = self._api_call('/routers', 'neutron')
            routers = routers_data.get('routers', [])
            
            return [{
                'id': router.get('id'),
                'name': router.get('name'),
                'status': router.get('status'),
                'admin_state_up': router.get('admin_state_up'),
                'external_gateway_info': router.get('external_gateway_info'),
                'ha': router.get('ha'),
                'distributed': router.get('distributed')
            } for router in routers]
            
        except Exception as e:
            print(f"Error listing routers: {e}")
            return []

    # ============ SERVER ANALYSIS (OPENSTACK NATIVE) ============
    
    def analyze_server_resources(self, server_id: str) -> Optional[Dict]:
        """Analyze server resource allocation and usage"""
        try:
            server = self.get_server_details(server_id)
            if not server:
                return None
            
            # Get flavor details for resource specs
            flavor_details = None
            if server.get('flavor'):
                flavor_details = self.get_flavor_details(server['flavor'])
            
            # Get hypervisor info if server is running
            hypervisor_info = None
            if server.get('host'):
                hypervisors = self.list_hypervisors()
                hypervisor_info = next((h for h in hypervisors if h.get('hypervisor_hostname') == server.get('host')), None)
            
            analysis = {
                "server_info": {
                    "id": server.get('id'),
                    "name": server.get('name'),
                    "status": server.get('status'),
                    "host": server.get('host'),
                    "created": server.get('created')
                },
                "resource_allocation": {},
                "host_analysis": {},
                "health_status": "unknown"
            }
            
            # Add flavor resource information
            if flavor_details:
                analysis["resource_allocation"] = {
                    "vcpus": flavor_details.get('vcpus'),
                    "ram_mb": flavor_details.get('ram'),
                    "disk_gb": flavor_details.get('disk'),
                    "ephemeral_gb": flavor_details.get('ephemeral', 0)
                }
            
            # Add hypervisor information
            if hypervisor_info:
                analysis["host_analysis"] = {
                    "hypervisor": hypervisor_info.get('hypervisor_hostname'),
                    "hypervisor_status": hypervisor_info.get('status'),
                    "hypervisor_state": hypervisor_info.get('state'),
                    "total_vcpus": hypervisor_info.get('vcpus'),
                    "used_vcpus": hypervisor_info.get('vcpus_used'),
                    "total_memory_mb": hypervisor_info.get('memory_mb'),
                    "used_memory_mb": hypervisor_info.get('memory_mb_used'),
                    "running_vms": hypervisor_info.get('running_vms')
                }
            
            # Determine health status
            if server.get('status') == 'ACTIVE' and server.get('power_state') == 1:
                analysis["health_status"] = "healthy"
            elif server.get('status') == 'ERROR':
                analysis["health_status"] = "error"
            elif server.get('status') in ['SHUTOFF', 'SUSPENDED']:
                analysis["health_status"] = "stopped"
            else:
                analysis["health_status"] = "transitioning"
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing server resources: {e}")
            return None

    # ============ INVENTORY REPORTING ============
    
    def generate_inventory_report(self, report_format: str = "detailed") -> Dict[str, Any]:
        """Generate comprehensive inventory report of all Openstack resources"""
        try:
            from datetime import datetime
            
            # Gather all inventory data
            servers = self.list_servers()
            hypervisors = self.list_hypervisors()
            flavors = self.list_flavors()
            images = self.list_images()
            volumes = self.list_volumes()
            volume_types = self.list_volume_types()
            networks = self.list_networks()
            subnets = self.list_subnets()
            routers = self.list_routers()
            
            # Generate timestamp
            report_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            
            # Base report structure
            inventory_report = {
                "report_metadata": {
                    "generated_at": report_timestamp,
                    "format": report_format,
                    "openstack_services": ["nova", "cinder", "neutron", "keystone"]
                },
                "summary": {},
                "compute": {},
                "storage": {},
                "networking": {},
                "resource_utilization": {},
                "recommendations": []
            }
            
            # ============ SUMMARY SECTION ============
            inventory_report["summary"] = {
                "total_resources": {
                    "servers": len(servers),
                    "hypervisors": len(hypervisors),
                    "flavors": len(flavors),
                    "images": len(images),
                    "volumes": len(volumes),
                    "networks": len(networks),
                    "subnets": len(subnets),
                    "routers": len(routers)
                },
                "server_status_breakdown": self._get_status_breakdown(servers, 'status'),
                "hypervisor_status_breakdown": self._get_status_breakdown(hypervisors, 'status')
            }
            
            # ============ COMPUTE SECTION ============
            total_vcpus = sum(h.get('vcpus', 0) for h in hypervisors)
            used_vcpus = sum(h.get('vcpus_used', 0) for h in hypervisors)
            total_memory_mb = sum(h.get('memory_mb', 0) for h in hypervisors)
            used_memory_mb = sum(h.get('memory_mb_used', 0) for h in hypervisors)
            total_disk_gb = sum(h.get('local_gb', 0) for h in hypervisors)
            used_disk_gb = sum(h.get('local_gb_used', 0) for h in hypervisors)
            
            inventory_report["compute"] = {
                "servers": {
                    "total": len(servers),
                    "by_status": self._get_status_breakdown(servers, 'status'),
                    "active_servers": len([s for s in servers if s.get('status') == 'ACTIVE']),
                    "error_servers": [s for s in servers if s.get('status') == 'ERROR']
                },
                "hypervisors": {
                    "total": len(hypervisors),
                    "enabled": len([h for h in hypervisors if h.get('status') == 'enabled']),
                    "capacity": {
                        "vcpus": {
                            "total": total_vcpus,
                            "used": used_vcpus,
                            "available": total_vcpus - used_vcpus,
                            "utilization_percent": round((used_vcpus / total_vcpus * 100), 2) if total_vcpus > 0 else 0
                        },
                        "memory": {
                            "total_mb": total_memory_mb,
                            "used_mb": used_memory_mb,
                            "available_mb": total_memory_mb - used_memory_mb,
                            "utilization_percent": round((used_memory_mb / total_memory_mb * 100), 2) if total_memory_mb > 0 else 0
                        },
                        "local_storage": {
                            "total_gb": total_disk_gb,
                            "used_gb": used_disk_gb,
                            "available_gb": total_disk_gb - used_disk_gb,
                            "utilization_percent": round((used_disk_gb / total_disk_gb * 100), 2) if total_disk_gb > 0 else 0
                        }
                    }
                },
                "flavors": {
                    "total": len(flavors),
                    "public_flavors": len([f for f in flavors if f.get('is_public')]),
                    "resource_specs": {
                        "smallest_vcpu": min((f.get('vcpus', 0) for f in flavors), default=0),
                        "largest_vcpu": max((f.get('vcpus', 0) for f in flavors), default=0),
                        "smallest_ram_mb": min((f.get('ram', 0) for f in flavors), default=0),
                        "largest_ram_mb": max((f.get('ram', 0) for f in flavors), default=0)
                    }
                }
            }
            
            # Add detailed server list if requested
            if report_format == "detailed":
                inventory_report["compute"]["server_details"] = servers
                inventory_report["compute"]["hypervisor_details"] = hypervisors
                inventory_report["compute"]["flavor_details"] = flavors
            
            # ============ STORAGE SECTION ============
            total_volume_size = sum(v.get('size', 0) for v in volumes)
            available_volumes = len([v for v in volumes if v.get('status') == 'available'])
            in_use_volumes = len([v for v in volumes if v.get('status') == 'in-use'])
            
            inventory_report["storage"] = {
                "volumes": {
                    "total": len(volumes),
                    "total_size_gb": total_volume_size,
                    "by_status": self._get_status_breakdown(volumes, 'status'),
                    "available": available_volumes,
                    "in_use": in_use_volumes,
                    "attachment_rate": round((in_use_volumes / len(volumes) * 100), 2) if volumes else 0
                },
                "volume_types": {
                    "total": len(volume_types),
                    "public_types": len([vt for vt in volume_types if vt.get('is_public')])
                }
            }
            
            if report_format == "detailed":
                inventory_report["storage"]["volume_details"] = volumes
                inventory_report["storage"]["volume_type_details"] = volume_types
            
            # ============ NETWORKING SECTION ============
            external_networks = len([n for n in networks if n.get('external')])
            internal_networks = len(networks) - external_networks
            
            inventory_report["networking"] = {
                "networks": {
                    "total": len(networks),
                    "external": external_networks,
                    "internal": internal_networks,
                    "shared": len([n for n in networks if n.get('shared')]),
                    "by_status": self._get_status_breakdown(networks, 'status')
                },
                "subnets": {
                    "total": len(subnets),
                    "ipv4": len([s for s in subnets if s.get('ip_version') == 4]),
                    "ipv6": len([s for s in subnets if s.get('ip_version') == 6]),
                    "dhcp_enabled": len([s for s in subnets if s.get('enable_dhcp')])
                },
                "routers": {
                    "total": len(routers),
                    "active": len([r for r in routers if r.get('status') == 'ACTIVE']),
                    "with_external_gateway": len([r for r in routers if r.get('external_gateway_info')])
                }
            }
            
            if report_format == "detailed":
                inventory_report["networking"]["network_details"] = networks
                inventory_report["networking"]["subnet_details"] = subnets
                inventory_report["networking"]["router_details"] = routers
            
            # ============ RESOURCE UTILIZATION ============
            inventory_report["resource_utilization"] = {
                "compute_utilization": {
                    "cpu_percent": round((used_vcpus / total_vcpus * 100), 2) if total_vcpus > 0 else 0,
                    "memory_percent": round((used_memory_mb / total_memory_mb * 100), 2) if total_memory_mb > 0 else 0,
                    "disk_percent": round((used_disk_gb / total_disk_gb * 100), 2) if total_disk_gb > 0 else 0
                },
                "high_utilization_hypervisors": [
                    h.get('hypervisor_hostname') for h in hypervisors 
                    if (h.get('vcpus_used', 0) / h.get('vcpus', 1)) > 0.8
                ],
                "servers_per_hypervisor": {
                    h.get('hypervisor_hostname'): h.get('running_vms', 0) 
                    for h in hypervisors
                }
            }
            
            # ============ RECOMMENDATIONS ============
            recommendations = []
            
            # CPU utilization recommendations
            if total_vcpus > 0 and (used_vcpus / total_vcpus) > 0.8:
                recommendations.append({
                    "type": "capacity_warning",
                    "resource": "CPU",
                    "message": f"CPU utilization is high ({round((used_vcpus / total_vcpus * 100), 2)}%). Consider adding more compute capacity.",
                    "priority": "high"
                })
            
            # Memory utilization recommendations
            if total_memory_mb > 0 and (used_memory_mb / total_memory_mb) > 0.8:
                recommendations.append({
                    "type": "capacity_warning",
                    "resource": "Memory",
                    "message": f"Memory utilization is high ({round((used_memory_mb / total_memory_mb * 100), 2)}%). Consider adding more memory or nodes.",
                    "priority": "high"
                })
            
            # Error servers recommendations
            error_servers = [s for s in servers if s.get('status') == 'ERROR']
            if error_servers:
                recommendations.append({
                    "type": "health_issue",
                    "resource": "Servers",
                    "message": f"{len(error_servers)} servers are in ERROR state. Investigation required.",
                    "priority": "critical",
                    "affected_servers": [s.get('name', s.get('id')) for s in error_servers]
                })
            
            # Disabled hypervisors recommendations
            disabled_hypervisors = [h for h in hypervisors if h.get('status') != 'enabled']
            if disabled_hypervisors:
                recommendations.append({
                    "type": "infrastructure_issue",
                    "resource": "Hypervisors",
                    "message": f"{len(disabled_hypervisors)} hypervisors are not enabled. Check hypervisor health.",
                    "priority": "medium",
                    "affected_hypervisors": [h.get('hypervisor_hostname') for h in disabled_hypervisors]
                })
            
            # Flavor optimization recommendations
            unused_flavors = []
            for flavor in flavors:
                flavor_used = any(s.get('flavor') == flavor.get('id') for s in servers)
                if not flavor_used and flavor.get('is_public'):
                    unused_flavors.append(flavor.get('name'))
            
            if unused_flavors:
                recommendations.append({
                    "type": "optimization",
                    "resource": "Flavors",
                    "message": f"{len(unused_flavors)} public flavors are unused. Consider cleanup.",
                    "priority": "low",
                    "unused_flavors": unused_flavors[:5]  # Limit to first 5
                })
            
            inventory_report["recommendations"] = recommendations
            
            return inventory_report
            
        except Exception as e:
            return {
                "error": f"Failed to generate inventory report: {str(e)}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            }
    
    def _get_status_breakdown(self, resources: List[Dict], status_field: str) -> Dict[str, int]:
        """Helper function to get status breakdown for resources"""
        status_count = {}
        for resource in resources:
            status = resource.get(status_field, 'unknown')
            status_count[status] = status_count.get(status, 0) + 1
        return status_count
