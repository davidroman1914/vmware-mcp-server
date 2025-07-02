# VMware VM Maintenance Procedures

## Kubernetes VM Power-Down Sequence

When shutting down Kubernetes VMs for maintenance:

1. **Kubernetes Worker Nodes**
   - Find all VMs with names containing "worker" or "node"
   - Power off all Kubernetes worker nodes

2. **Kubernetes Master Nodes**
   - Find all VMs with names containing "master" or "control-plane"
   - Power off all Kubernetes master nodes

## Kubernetes VM Power-Up Sequence

When starting up Kubernetes VMs after maintenance:

1. **Kubernetes Master Nodes**
   - Power on Kubernetes master nodes first

2. **Kubernetes Worker Nodes**
   - Power on Kubernetes worker nodes

## Maintenance Mode Procedures

### Pre-Maintenance Checklist
- Verify all VMs are in a healthy state

### During Maintenance
- Power off VMs in reverse dependency order
- Power on VMs in dependency order
- Verify each VM starts successfully before proceeding

### Post-Maintenance Verification
- Check all services are running
- Verify network connectivity

## Emergency Restart Procedures

In case of emergency:
1. Power off all VMs immediately
2. Wait 60 seconds
3. Power on VMs in standard restart sequence
4. Monitor for any startup issues 