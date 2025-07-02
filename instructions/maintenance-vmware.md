# VMware VM Maintenance Procedures

## VM Power-Down Sequence

When shutting down VMs for maintenance:

1. **Wave 1 - Worker Nodes**
   We will power off all the VMs with the following names or selectors in our list below. 
   - workers or node 

2. **Wave 2 - Control Plane**
   We will power off all the VMs with the following names or selectors in our list below. 
   - master or control-plane

3. **Wave 3 - Remaining VMs**
   We will power off all remaining VMs not already powered off.

## VM Power-Up Sequence

When starting up VMs after maintenance:

1. **Wave 1 - Control Plane**
   We will power on all the VMs with the following names or selectors in our list below. 
   - master or control-plane

2. **Wave 2 - Worker Nodes**
   We will power on all the VMs with the following names or selectors in our list below. 
   - workers or node 

3. **Wave 3 - Applications**
   We will power on all remaining VMs not already powered on.

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