"""Exact WF lease types and their isolated campaign roots.

Registration and the chained pending-unit lease are still checked by each
permit's validate/validate_d methods. Being listed here grants no activation.
"""


def authorized_wf_permits():
    from btc_risk_rl.pilots import (
        wf_cost,
        wf_cost_replacement_03_exec,
        wf_cost_replacement_04_exec,
        wf_cost_replacement_exec,
    )

    return {
        wf_cost.WFCostPermit: wf_cost.CAMPAIGN,
        wf_cost_replacement_exec.WFCostPermit: wf_cost_replacement_exec.CAMPAIGN,
        wf_cost_replacement_03_exec.WFCostPermit: wf_cost_replacement_03_exec.CAMPAIGN,
        wf_cost_replacement_04_exec.WFCostPermit: wf_cost_replacement_04_exec.CAMPAIGN,
    }
