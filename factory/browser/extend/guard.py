"""Not a patch. default_action_watchdog.py:876 and :1815 both do: if is_occluded ->
Runtime.callFunctionOn "function(){this.click();}" -- detection whose consequence is dispatch
anyway. So we do not route clicks through ClickElementEvent; we hit-test and dispatch ourselves.
Their _check_element_occlusion (:573) is worth porting for one thing only: a label stands for
its input.
"""
