"""
PCBO Engine — детерминированный пайплайн синтеза и верификации PC-сборок.

Онтология: ontology/.
База компонентов: examples/kb/ (демо) или kaizin-lab/pc_hardware_knowledge_base.

Пайплайн:
1. verify_structural_clearance  — геометрия (GPU/кулер/корпус)
2. evaluate_pcie_topology       — линии PCIe, бифуркация, DRAM-less SSD
3. simulate_thermal_profiles    — взаимный нагрев, ambient
4. evaluate_marginal_value      — MV = ΔPerf% / ΔPrice%, правило AR-03
5. calculate_power_states       — TDP, ATX 3.0, transient spikes
6. assess_acoustic_class        — класс шума, DPC latency
7. validate_l5_rules            — агрегатор, rollback trigger
8. validate_profile_conflicts   — BLOCK/WARN по профилям компонентов
9. validate_physical_constraints — бинарные физические предикаты
10. validate_mvs_allocation      — распределение бюджета
11. validate_cpu_vrm             — CPU TDP → VRM платы
12. validate_gpu_pcie            — класс GPU → слот платы
13. validate_component_floor     — минимальные требования интента
14. pass_contract                — трассировка контрактов и SKIP/FAIL
"""
