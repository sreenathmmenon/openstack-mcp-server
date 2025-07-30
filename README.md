# OpenStack MCP Server

A comprehensive Model Context Protocol (MCP) server for OpenStack cloud management. This server provides AI tools for compute, storage, networking, and resource analysis, enabling natural language interactions with OpenStack infrastructure.

## Features

### **17 Comprehensive Tools**

#### Compute Management
- `list_servers` - List all virtual machines with status and configuration
- `get_server_details` - Get detailed VM information including resources and metadata
- `list_hypervisors` - View hypervisor hosts with resource usage and capacity
- `list_flavors` - List compute templates with resource specifications
- `get_flavor_details` - Get detailed flavor information with extra specs

#### Image Management  
- `list_images` - List all VM images with status and properties
- `get_image_details` - Get detailed image information and metadata

#### Storage Management
- `list_volumes` - List storage volumes with status and attachment info
- `list_volume_types` - List volume types with specifications

#### Network Management
- `list_networks` - List networks with status and configuration
- `list_subnets` - List subnets with CIDR and DHCP configuration  
- `list_routers` - List routers with status and gateway info

#### Infrastructure Analysis
- `analyze_server_resources` - Server resource allocation and hypervisor analysis
- `get_infrastructure_summary` - Comprehensive infrastructure overview
- `get_resource_utilization` - Detailed resource usage across hypervisors
- `check_service_health` - Health status of OpenStack services

#### Reporting Tools
- `generate_inventory_report` - Comprehensive inventory report with utilization metrics and recommendations

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-username/openstack-mcp-server.git
cd openstack-mcp-server
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure OpenStack credentials**

Option A: Using configuration file
```bash
cp config.json.example config.json
# Edit config.json with your OpenStack credentials
```

Option B: Using environment variables
```bash
export OS_AUTH_URL="https://your-openstack:5000/v3"
export OS_USERNAME="admin"
export OS_PASSWORD="your-password"
export OS_PROJECT_NAME="admin"
export OS_USER_DOMAIN_NAME="Default"
```

## 🚀 Usage

### **Option 1: Standard MCP Server**
```bash
# Run standard MCP server
python openstack_mcp_server.py [config.json]

# With environment configuration
OPENSTACK_CONFIG_PATH=config.json python openstack_mcp_server.py

# Test the server
python test_client.py
python test_client.py --interactive
```

### **Option 2: FastMCP Server** (Simpler for Development)
```bash
# Install FastMCP (optional)
pip install git+https://github.com/jlowin/fastmcp.git

# Run FastMCP server
python openstack_fastmcp_server.py [config.json]

# Test FastMCP tools directly
python test_fastmcp.py
```

### Example MCP Client Integration
```python
from mcp.client.stdio import StdioServerParameters, stdio_client

async def use_openstack_mcp():
    server_params = StdioServerParameters(
        command="python",
        args=["openstack_mcp_server.py"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        await read.initialize()
        
        # List available tools
        tools = await read.list_tools()
        print(f"Available tools: {len(tools.tools)}")
        
        # Get all servers
        result = await read.call_tool("list_servers", {})
        servers = json.loads(result.content[0].text)
        print(f"Found {len(servers)} servers")
        
        # Analyze a specific server
        result = await read.call_tool("analyze_server_resources", {"server_id": "server-uuid"})
        analysis = json.loads(result.content[0].text)
        print(f"Server analysis: {analysis}")
        
        # Generate comprehensive inventory report
        result = await read.call_tool("generate_inventory_report", {"format": "detailed"})
        report = json.loads(result.content[0].text)
        print(f"Inventory report generated at: {report['report_metadata']['generated_at']}")
```

## 📋 Configuration Options

### Config File Format (config.json)
```json
{
    "AUTH_URL": "https://your-openstack:5000/v3",
    "USERNAME": "admin", 
    "PASSWORD": "your-password",
    "PROJECT": "admin",
    "DOMAIN": "Default"
}
```

### Environment Variables
- `OS_AUTH_URL` - Keystone authentication URL
- `OS_USERNAME` - OpenStack username
- `OS_PASSWORD` - OpenStack password  
- `OS_PROJECT_NAME` - OpenStack project name
- `OS_USER_DOMAIN_NAME` - OpenStack domain name
- `OPENSTACK_CONFIG_PATH` - Path to config file

## 🔧 API Coverage

### OpenStack Services
- **Nova** (Compute) - Full server, hypervisor, and flavor management
- **Cinder** (Block Storage) - Volume and volume type operations  
- **Neutron** (Networking) - Network, subnet, and router management
- **Keystone** (Identity) - Authentication and token management

### Supported Operations
- ✅ List and detail operations for all resources
- ✅ Resource utilization monitoring
- ✅ Service health checking
- ✅ Infrastructure summarization
- ✅ Server resource analysis and placement optimization
- ✅ Comprehensive inventory reporting with recommendations
- ✅ Error handling and recovery

## 📊 Inventory Report Features

The `generate_inventory_report` tool provides comprehensive OpenStack environment analysis:

### **Report Sections**
- **Summary** - Resource counts and status breakdowns
- **Compute** - Server, hypervisor, and flavor analysis with capacity metrics
- **Storage** - Volume usage, types, and attachment rates
- **Networking** - Network, subnet, and router configurations
- **Resource Utilization** - CPU, memory, and storage utilization percentages
- **Recommendations** - AI-powered optimization suggestions

### **Report Formats**
- `summary` - High-level overview and key metrics
- `detailed` - Complete resource listings and detailed analysis

### **Generated Recommendations**
- **Capacity Warnings** - High utilization alerts (>80%)
- **Health Issues** - Error servers and failed components
- **Infrastructure Issues** - Disabled hypervisors and service problems
- **Optimization Tips** - Unused flavors and resource cleanup suggestions

### **Example Report Structure**
```json
{
  "report_metadata": {
    "generated_at": "2024-01-15 14:30:00 UTC",
    "format": "detailed",
    "openstack_services": ["nova", "cinder", "neutron", "keystone"]
  },
  "summary": {
    "total_resources": {
      "servers": 45,
      "hypervisors": 8,
      "volumes": 23,
      "networks": 12
    }
  },
  "compute": {
    "servers": {
      "total": 45,
      "active_servers": 42,
      "error_servers": []
    },
    "hypervisors": {
      "capacity": {
        "vcpus": {
          "total": 320,
          "used": 180,
          "utilization_percent": 56.25
        }
      }
    }
  },
  "recommendations": [
    {
      "type": "capacity_warning",
      "resource": "CPU",
      "message": "CPU utilization is high (85%). Consider adding more compute capacity.",
      "priority": "high"
    }
  ]
}
```

## 🏗️ Architecture

```
┌─────────────────────┐
│   MCP Client        │
│   (AI Assistant)    │
└──────────┬──────────┘
           │ MCP Protocol
┌──────────▼──────────┐
│ OpenStack MCP Server│
├─────────────────────┤
│ • Tool Definitions  │
│ • Request Handlers  │
│ • Error Management  │
└──────────┬──────────┘
           │ REST APIs
┌──────────▼──────────┐
│ OpenStack Client    │
├─────────────────────┤
│ • Nova (Compute)    │
│ • Cinder (Storage)  │
│ • Neutron (Network) │ 
│ • Keystone (Auth)   │
└─────────────────────┘
```

## 🎯 Use Cases

### AI-Powered Infrastructure Management
- Natural language queries about infrastructure
- Automated troubleshooting and diagnostics
- Resource optimization recommendations
- Capacity planning assistance

### Example Queries
- "Show me all running VMs and their resource usage"
- "Which hypervisors are approaching capacity limits?"
- "What's the health status of my OpenStack services?"
- "Analyze the resource allocation for server xyz-123"
- "Generate a comprehensive inventory report of my OpenStack environment"
- "Which servers are consuming the most resources?"
- "Show me optimization recommendations for my infrastructure"

## 🔒 Security Considerations

- Use environment variables for production credentials
- Enable SSL verification for production deployments
- Implement proper authentication and authorization
- Monitor and log API access

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built on the Model Context Protocol (MCP) framework
- Inspired by the need for AI-powered infrastructure management
- Designed for OpenStack cloud environments

---

**Author:** Sreenath  
**Repository:** https://github.com/your-username/openstack-mcp-server  
**Issues:** https://github.com/your-username/openstack-mcp-server/issues
