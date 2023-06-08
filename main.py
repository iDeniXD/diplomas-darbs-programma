import json
from classes.classes import ResultEncoder
from globals import initialize
from scenario_executor import run_steps
from loggers.result_logger import log

"""I was expecting this import to prevent the debugger from stopping in try-catch blocks, but
it just made the debugging worse by catching exceptions in a weird way. Do not recommend to 
uncomment this block"""
# try:  
#     from pydevd import GetGlobalDebugger
#     GetGlobalDebugger().skip_on_exceptions_thrown_in_same_context = True
# except:
#     pass



scenario, driver = initialize()

result = run_steps(driver, scenario["steps"], '', [])

resultJSONData = json.dumps(result, indent=4, cls=ResultEncoder)

print(resultJSONData) # max 16383
log(resultJSONData)
print('end')