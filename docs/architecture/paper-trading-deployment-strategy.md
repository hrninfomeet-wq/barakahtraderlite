# Paper Trading Deployment Strategy

## Executive Summary

This document defines a phased deployment strategy with feature flags and rollback procedures to mitigate deployment complexity risks (OPS-001) for Story 2.1.

## 1. Deployment Architecture

### 1.1 Environment Strategy

```yaml
# deployment/environments.yaml
environments:
  development:
    name: dev
    url: https://dev.trading.internal
    features:
      paper_trading: enabled
      live_trading: disabled
      mode_switching: enabled
    database:
      paper_schema: paper_trading_dev
      live_schema: null  # No live in dev
    monitoring:
      level: debug
      alerts: disabled
  
  staging:
    name: staging
    url: https://staging.trading.internal
    features:
      paper_trading: enabled
      live_trading: enabled
      mode_switching: enabled
    database:
      paper_schema: paper_trading_staging
      live_schema: live_trading_staging
    monitoring:
      level: info
      alerts: enabled
      
  production:
    name: production
    url: https://trading.example.com
    features:
      paper_trading: enabled
      live_trading: disabled  # Initially disabled
      mode_switching: disabled  # Initially disabled
    database:
      paper_schema: paper_trading_prod
      live_schema: live_trading_prod
    monitoring:
      level: warning
      alerts: enabled
      pagerduty: enabled
```

### 1.2 Feature Flag System

```python
# backend/core/feature_flags.py
import os
from enum import Enum
from typing import Dict, Any, Optional
import json
from datetime import datetime
import redis

class FeatureFlag(Enum):
    """Feature flags for paper trading deployment"""
    PAPER_TRADING_ENABLED = "paper_trading_enabled"
    LIVE_TRADING_ENABLED = "live_trading_enabled"
    MODE_SWITCHING_ENABLED = "mode_switching_enabled"
    SIMULATION_ACCURACY_MONITORING = "simulation_accuracy_monitoring"
    ADVANCED_UX_FEATURES = "advanced_ux_features"
    EMERGENCY_STOP_ENABLED = "emergency_stop_enabled"

class FeatureFlagManager:
    """Manages feature flags with remote configuration"""
    
    def __init__(self):
        self.redis_client = redis.Redis()
        self.cache_ttl = 60  # 1 minute cache
        self.default_flags = {
            FeatureFlag.PAPER_TRADING_ENABLED: True,
            FeatureFlag.LIVE_TRADING_ENABLED: False,
            FeatureFlag.MODE_SWITCHING_ENABLED: False,
            FeatureFlag.SIMULATION_ACCURACY_MONITORING: True,
            FeatureFlag.ADVANCED_UX_FEATURES: False,
            FeatureFlag.EMERGENCY_STOP_ENABLED: True,
        }
        
    def is_enabled(
        self, 
        flag: FeatureFlag,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if feature flag is enabled"""
        
        # Check emergency override
        if self._check_emergency_override(flag):
            return False
        
        # Check user-specific flags
        if user_id and self._check_user_flag(flag, user_id):
            return True
        
        # Check percentage rollout
        if self._check_percentage_rollout(flag, user_id):
            return True
        
        # Check environment-specific flags
        env_flag = self._get_environment_flag(flag)
        if env_flag is not None:
            return env_flag
        
        # Return default
        return self.default_flags.get(flag, False)
    
    def _check_percentage_rollout(
        self, 
        flag: FeatureFlag,
        user_id: Optional[str]
    ) -> bool:
        """Check if user is in percentage rollout"""
        
        rollout_config = self._get_rollout_config(flag)
        if not rollout_config:
            return False
        
        percentage = rollout_config.get("percentage", 0)
        if percentage == 0:
            return False
        if percentage >= 100:
            return True
        
        # Use consistent hashing for user assignment
        if user_id:
            hash_value = hash(f"{flag.value}:{user_id}") % 100
            return hash_value < percentage
        
        return False
    
    def _get_rollout_config(self, flag: FeatureFlag) -> Optional[Dict]:
        """Get rollout configuration from Redis"""
        
        key = f"feature_flag:rollout:{flag.value}"
        config = self.redis_client.get(key)
        
        if config:
            return json.loads(config)
        return None
    
    def set_rollout_percentage(
        self,
        flag: FeatureFlag,
        percentage: int
    ):
        """Set rollout percentage for feature flag"""
        
        config = {
            "percentage": max(0, min(100, percentage)),
            "updated_at": datetime.now().isoformat(),
            "updated_by": "deployment_system"
        }
        
        key = f"feature_flag:rollout:{flag.value}"
        self.redis_client.setex(
            key,
            86400,  # 24 hours
            json.dumps(config)
        )
        
        # Log configuration change
        self._log_flag_change(flag, config)
```

## 2. Phased Deployment Plan

### 2.1 Phase 1: Paper Trading Only (Week 1)

```yaml
# deployment/phase1.yaml
phase: 1
name: "Paper Trading Foundation"
duration: "1 week"
features:
  enabled:
    - paper_trading_engine
    - virtual_portfolio
    - simulation_accuracy_monitoring
    - basic_ui
  disabled:
    - live_trading
    - mode_switching
    - advanced_ux
rollout:
  strategy: "all_users"
  percentage: 100
validation:
  - simulation_accuracy >= 95%
  - no_critical_errors
  - user_feedback_positive
rollback_trigger:
  - simulation_accuracy < 90%
  - critical_errors > 0
  - system_instability
```

### 2.2 Phase 2: Limited Mode Switching (Week 2)

```yaml
# deployment/phase2.yaml
phase: 2
name: "Mode Switching Beta"
duration: "1 week"
features:
  enabled:
    - paper_trading_engine
    - mode_switching
    - enhanced_security
  disabled:
    - live_trading  # Still disabled
rollout:
  strategy: "percentage"
  percentage: 10  # 10% of users
  criteria:
    - experienced_users
    - completed_tutorial
validation:
  - mode_switch_success_rate >= 99%
  - no_accidental_mode_switches
  - security_validations_pass
```

### 2.3 Phase 3: Live Trading Beta (Week 3)

```yaml
# deployment/phase3.yaml
phase: 3
name: "Live Trading Beta"
duration: "2 weeks"
features:
  enabled:
    - paper_trading_engine
    - mode_switching
    - live_trading
    - emergency_stop
rollout:
  strategy: "whitelist"
  users:
    - beta_testers
    - internal_team
  percentage: 5  # 5% of total users
validation:
  - no_paper_to_live_leaks
  - mode_validation_100%
  - user_verification_working
```

### 2.4 Phase 4: General Availability (Week 5)

```yaml
# deployment/phase4.yaml
phase: 4
name: "General Availability"
duration: "ongoing"
features:
  enabled:
    - all_features
rollout:
  strategy: "gradual"
  schedule:
    - day_1: 25%
    - day_3: 50%
    - day_5: 75%
    - day_7: 100%
monitoring:
  - continuous
  - real_time_alerts
  - automatic_rollback
```

## 3. Deployment Automation

### 3.1 CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy Paper Trading

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - development
          - staging
          - production
      phase:
        description: 'Deployment phase'
        required: true
        default: '1'
        type: choice
        options:
          - '1'
          - '2'
          - '3'
          - '4'

jobs:
  pre-deployment:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Run tests
        run: |
          python -m pytest backend/tests/
          npm test frontend/
      
      - name: Security scan
        run: |
          pip install safety
          safety check
      
      - name: Build artifacts
        run: |
          docker build -t paper-trading:${{ github.sha }} .
          
  deploy:
    needs: pre-deployment
    runs-on: ubuntu-latest
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-south-1
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster trading-cluster \
            --service paper-trading-${{ inputs.environment }} \
            --force-new-deployment
      
      - name: Update feature flags
        run: |
          python scripts/update_feature_flags.py \
            --environment ${{ inputs.environment }} \
            --phase ${{ inputs.phase }}
      
      - name: Health check
        run: |
          python scripts/health_check.py \
            --environment ${{ inputs.environment }} \
            --timeout 300
```

### 3.2 Rollback Procedures

```python
# scripts/rollback.py
import boto3
import time
from typing import Dict, Any
import sys

class RollbackManager:
    """Manages deployment rollbacks"""
    
    def __init__(self, environment: str):
        self.environment = environment
        self.ecs_client = boto3.client('ecs')
        self.cloudwatch = boto3.client('cloudwatch')
        
    def should_rollback(self) -> bool:
        """Check if rollback is needed"""
        
        metrics = self.get_health_metrics()
        
        # Check critical metrics
        if metrics['error_rate'] > 0.01:  # >1% error rate
            return True
        
        if metrics['response_time_p99'] > 1000:  # >1s p99 latency
            return True
        
        if metrics['simulation_accuracy'] < 0.90:  # <90% accuracy
            return True
        
        if metrics['mode_validation_failures'] > 0:
            return True
        
        return False
    
    def execute_rollback(self):
        """Execute rollback to previous version"""
        
        print(f"Initiating rollback for {self.environment}")
        
        # Get previous task definition
        previous_task = self.get_previous_task_definition()
        
        # Update service with previous version
        response = self.ecs_client.update_service(
            cluster=f'trading-cluster',
            service=f'paper-trading-{self.environment}',
            taskDefinition=previous_task
        )
        
        # Disable problematic feature flags
        self.disable_feature_flags()
        
        # Wait for rollback to complete
        self.wait_for_stable_state()
        
        # Send alerts
        self.send_rollback_alert()
        
        print("Rollback completed successfully")
    
    def disable_feature_flags(self):
        """Disable risky feature flags"""
        
        flags_to_disable = [
            'live_trading_enabled',
            'mode_switching_enabled',
            'advanced_ux_features'
        ]
        
        for flag in flags_to_disable:
            self.update_feature_flag(flag, enabled=False)
    
    def wait_for_stable_state(self, timeout: int = 300):
        """Wait for service to stabilize"""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_service_stable():
                return True
            time.sleep(10)
        
        raise TimeoutError("Service did not stabilize after rollback")
```

## 4. Monitoring and Alerts

### 4.1 Deployment Metrics

```python
# backend/monitoring/deployment_metrics.py
from dataclasses import dataclass
from typing import List, Dict
import prometheus_client as prom

@dataclass
class DeploymentMetrics:
    """Metrics for deployment monitoring"""
    
    # Deployment progress
    deployment_phase = prom.Gauge(
        'deployment_phase',
        'Current deployment phase',
        ['environment']
    )
    
    # Feature flag status
    feature_flag_enabled = prom.Gauge(
        'feature_flag_enabled',
        'Feature flag status',
        ['flag_name', 'environment']
    )
    
    # Rollout percentage
    rollout_percentage = prom.Gauge(
        'rollout_percentage',
        'Feature rollout percentage',
        ['feature', 'environment']
    )
    
    # Mode switching metrics
    mode_switches = prom.Counter(
        'mode_switches_total',
        'Total mode switches',
        ['from_mode', 'to_mode', 'status']
    )
    
    # Deployment health
    deployment_health = prom.Gauge(
        'deployment_health_score',
        'Overall deployment health score',
        ['environment']
    )
    
    # Rollback events
    rollbacks = prom.Counter(
        'deployment_rollbacks_total',
        'Total deployment rollbacks',
        ['environment', 'reason']
    )
```

### 4.2 Alert Configuration

```yaml
# monitoring/alerts.yaml
alerts:
  - name: DeploymentErrorRate
    condition: error_rate > 0.01
    duration: 5m
    severity: critical
    action: 
      - rollback
      - page_oncall
    
  - name: SimulationAccuracyLow
    condition: simulation_accuracy < 0.90
    duration: 10m
    severity: warning
    action:
      - notify_team
      - investigate
  
  - name: ModeValidationFailure
    condition: mode_validation_failures > 0
    duration: 1m
    severity: critical
    action:
      - disable_mode_switching
      - rollback
      - page_oncall
  
  - name: DeploymentStuck
    condition: deployment_duration > 30m
    severity: warning
    action:
      - notify_team
      - check_health
```

## 5. Integration Testing in Staging

### 5.1 Staging Test Suite

```python
# tests/staging/test_deployment.py
import pytest
import asyncio
from typing import Dict, Any

class TestStagingDeployment:
    """Integration tests for staging deployment"""
    
    @pytest.mark.staging
    async def test_paper_trading_isolation(self):
        """Verify paper trading is completely isolated"""
        
        # Create paper order
        paper_order = await self.create_paper_order()
        
        # Verify order is in paper schema only
        assert await self.check_paper_schema(paper_order.id)
        assert not await self.check_live_schema(paper_order.id)
        
        # Verify no live API calls made
        api_logs = await self.get_api_logs()
        assert not any(log['api'] == 'live' for log in api_logs)
    
    @pytest.mark.staging
    async def test_mode_switching_security(self):
        """Test mode switching security measures"""
        
        # Attempt switch without verification
        result = await self.switch_mode('PAPER', 'LIVE')
        assert result['status'] == 'verification_required'
        
        # Complete verification
        await self.complete_verification()
        
        # Attempt switch with verification
        result = await self.switch_mode('PAPER', 'LIVE')
        assert result['status'] == 'success'
        assert result['mode'] == 'LIVE'
    
    @pytest.mark.staging
    async def test_rollback_procedure(self):
        """Test automatic rollback on errors"""
        
        # Simulate high error rate
        await self.simulate_errors(rate=0.02)
        
        # Wait for rollback
        await asyncio.sleep(60)
        
        # Verify rollback occurred
        deployment_status = await self.get_deployment_status()
        assert deployment_status['rolled_back'] == True
        assert deployment_status['rollback_reason'] == 'high_error_rate'
```

## 6. Production Deployment Checklist

### 6.1 Pre-Deployment

```markdown
## Pre-Deployment Checklist

### Code Quality
- [ ] All tests passing (unit, integration, e2e)
- [ ] Code coverage > 80%
- [ ] Security scan completed
- [ ] Performance benchmarks met
- [ ] Documentation updated

### Infrastructure
- [ ] Database migrations tested
- [ ] Redis cache configured
- [ ] Load balancer configured
- [ ] SSL certificates valid
- [ ] Backup procedures tested

### Feature Flags
- [ ] All flags set to safe defaults
- [ ] Rollout percentages configured
- [ ] Emergency kill switches tested
- [ ] Flag management UI accessible

### Monitoring
- [ ] Metrics dashboards created
- [ ] Alerts configured
- [ ] Log aggregation working
- [ ] APM tools integrated
- [ ] Error tracking enabled
```

### 6.2 Deployment Execution

```markdown
## Deployment Execution Checklist

### Phase 1: Preparation
- [ ] Notify team of deployment
- [ ] Enable maintenance mode (if needed)
- [ ] Take database backup
- [ ] Record current metrics baseline

### Phase 2: Deployment
- [ ] Deploy to canary instance
- [ ] Run smoke tests
- [ ] Monitor metrics for 15 minutes
- [ ] Deploy to 10% of instances
- [ ] Monitor for 30 minutes
- [ ] Deploy to 50% of instances
- [ ] Monitor for 30 minutes
- [ ] Deploy to 100% of instances

### Phase 3: Validation
- [ ] Run full integration tests
- [ ] Verify all features working
- [ ] Check performance metrics
- [ ] Validate security measures
- [ ] Confirm data integrity

### Phase 4: Post-Deployment
- [ ] Update status page
- [ ] Send deployment notification
- [ ] Document any issues
- [ ] Schedule retrospective
```

## 7. Disaster Recovery

### 7.1 Recovery Procedures

```python
# scripts/disaster_recovery.py
class DisasterRecovery:
    """Disaster recovery procedures"""
    
    def execute_recovery(self, scenario: str):
        """Execute recovery based on scenario"""
        
        procedures = {
            "data_corruption": self.recover_from_data_corruption,
            "mode_confusion": self.recover_from_mode_confusion,
            "api_breach": self.recover_from_api_breach,
            "complete_failure": self.recover_from_complete_failure
        }
        
        recovery_func = procedures.get(scenario)
        if recovery_func:
            recovery_func()
        else:
            raise ValueError(f"Unknown scenario: {scenario}")
    
    def recover_from_mode_confusion(self):
        """Recover from paper/live mode confusion"""
        
        # 1. Immediately disable all trading
        self.emergency_stop()
        
        # 2. Set all users to paper mode
        self.force_all_users_to_paper()
        
        # 3. Audit all recent transactions
        suspicious_trades = self.audit_recent_trades()
        
        # 4. Reverse any paper trades that went live
        for trade in suspicious_trades:
            if trade.should_be_paper and trade.executed_live:
                self.reverse_trade(trade)
        
        # 5. Re-enable paper trading only
        self.enable_paper_trading_only()
        
        # 6. Notify affected users
        self.notify_affected_users(suspicious_trades)
```

## 8. Risk Mitigation Summary

This deployment strategy addresses OPS-001 (High Risk) by:

1. **Phased deployment** minimizes risk exposure
2. **Feature flags** enable gradual rollout and quick disable
3. **Automated rollback** reduces recovery time
4. **Comprehensive monitoring** detects issues early
5. **Disaster recovery** procedures handle worst-case scenarios

## 9. Implementation Timeline

| Week | Phase | Activities | Success Criteria |
|------|-------|------------|------------------|
| 1 | Phase 1 | Deploy paper trading only | 95% accuracy, stable |
| 2 | Phase 2 | Enable mode switching (10%) | No confusion incidents |
| 3-4 | Phase 3 | Live trading beta (5%) | Zero paper/live leaks |
| 5+ | Phase 4 | General availability | <0.1% error rate |

## 10. Next Steps

1. Set up feature flag infrastructure
2. Configure monitoring dashboards
3. Create rollback automation
4. Prepare staging environment
5. Document runbooks
