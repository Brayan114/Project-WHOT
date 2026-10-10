# WHOT-ML: A Configurable Partially Observable Multi-Agent Environment for Machine Learning Research

**WHOT-ML** is an open-source, deterministic, and modular multi-agent reinforcement learning environment based on **WHOT**, the widely played card game in Nigeria. Designed as a rigorous benchmark for research under partial observability, non-stationarity, and dynamic action masking, WHOT-ML formalizes the game as an extensive-form multi-agent POMDP. The platform guarantees strict information isolation (zero private-card leakage), bitwise deterministic reproducibility, configurable rule mechanics, and a standardized 76-slot discrete action space.

---

## What is WHOT-ML?

WHOT is a competitive shedding card game played with a dedicated 54-card deck of geometric suits (Circle, Triangle, Cross, Square, Star) and wild "WHOT" cards. Players match cards by shape or face value while deploying tactical special effects—such as chaining draw penalties ("Pick Two", "Pick Three"), skipping opponents ("Suspension"), forcing table-wide draws ("General Market"), or commanding new active suits. 

Crucially, players hold private hands, draw from a hidden deck that reshuffles upon depletion, and must declare before playing their final card. These mechanics generate deep information asymmetry, belief estimation challenges ($|\mathcal{S}(\Omega)| > 10^{32}$ states consistent with typical observations), and complex multi-agent defense dynamics.

---

## What's in This Repository?

- **`whot_ml/`** — Core simulation engine (`WHOT-NG-v1.0`, v1.0.0, frozen baseline at commit `7c1a2dc`). Includes state managers, turn sequencing, legal action masking, and baseline agents (`RandomLegalAgent`, `RuleBasedAgent`).
- **`tests/`** — Comprehensive test suite containing 109 unit, integration, and property invariant tests.
- **`experiments/paper1/`** — Experimental harnesses, formal JSON configurations, analysis scripts, and publication figures/tables for the Paper 1 evaluation campaign.
- **`docs/`** — Formal Phase 0/1 specifications, rules ontology, mathematical proofs, and independent scientific audits.
- **`WHOT-ML Paper 1 — Manuscript v1.0.md`** — Full research manuscript ready for preprint and peer review.
- **`CITATION.cff`** — Machine-readable citation metadata.
- **`LICENSE`** — Permissive MIT open-source license.

---

## Installation

WHOT-ML requires Python 3.9 or higher.

```bash
# Clone repository
git clone https://github.com/Brayan114/Project-WHOT.git
cd Project-WHOT

# Install dependencies
pip install -r requirements-paper1.txt
```

---

## Quick Start

### 1. Run the Test Suite
Verify that all 109 unit tests and environment invariants pass:
```bash
pytest tests/
```

### 2. Run a Quick Experiment (Smoke Test)
Execute a fast 5-game smoke test of the Paper 1 characterization benchmark:
```bash
python experiments/paper1/run_experiments.py --smoke-test
```

### 3. Basic Simulator Usage
```python
from whot_ml import WHOTEnvironment, WHOTConfig, RandomLegalAgent

# Initialize environment with default 4-player configuration
config = WHOTConfig(player_count=4, seed=42)
env = WHOTEnvironment(config=config)
obs = env.reset(seed=42)

agents = [RandomLegalAgent(p) for p in range(4)]

while not env.state.is_terminal:
    current_player = env.state.current_player
    legal_mask = env.get_legal_action_mask(current_player)
    action = agents[current_player].select_action(obs[current_player], legal_mask)
    step_result = env.step(action)
    obs = step_result.observations

print(f"Game completed in {env.state.turn_count} turns. Winner: Player {env.state.winner}")
```

---

## Reproducibility & Scientific Integrity

All experiments in WHOT-ML Paper 1 were executed under a strict frozen-baseline protocol:

- **Frozen Commit:** `7c1a2dc23a277fdfb5e9052d4d90e3798fb24ea4`
- **Environment:** `WHOT-NG-v1.0` (Simulator Version `1.0.0`)
- **Production Workload:** $N = 12,350$ games executed in isolated Linux cloud containers.
- **Audit Reports:** Complete independent scientific audits and claim verifications are available in [`docs/`](docs/).
- **Open Data:** Raw trajectory telemetry and artifact archives are deposited on Zenodo.

---

## Citation

If you use WHOT-ML in your research, please cite our work using the metadata in [`CITATION.cff`](CITATION.cff):

```bibtex
@article{osinaka2026whotml,
  title   = {WHOT-ML: A Configurable Partially Observable Multi-Agent Environment for Machine Learning Research},
  author  = {Osinaka, Brayan},
  journal = {Preprint / Zenodo},
  year    = {2026},
  doi     = {10.5281/zenodo.REPLACE-WITH-DOI-AFTER-ZENODO-RELEASE},
  url     = {https://github.com/Brayan114/Project-WHOT}
}
```

---

## License

This project is licensed under the terms of the **MIT License**. See [`LICENSE`](LICENSE) for details.

---

## Contact & Contributing

For questions, discussions, or bug reports, please open an issue on the [GitHub Issues](https://github.com/Brayan114/Project-WHOT/issues) tracker.
