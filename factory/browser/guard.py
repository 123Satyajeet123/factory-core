"""Ours, beside hit.py. Not a vendor extension: default_action_watchdog.py:876 and :1815 both do
`if is_occluded -> Runtime.callFunctionOn "function(){this.click();}"`, so we do not route
clicks through ClickElementEvent at all. Worth porting from their _check_element_occlusion
(:573): a label stands for its input.
"""
