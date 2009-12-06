"""
Author: Armon Dadgar
Description:
  This module is designed to help dynamically link against other modules,
  and to provide a import like functionality in repy.

  Its main mechanisms are dyn_import_module, dyn_import_module_symbols and dyn_dispatch_module.
  dyn_import_module_symbols allows importing directly into the current context (ala from X import *)
  and dyn_import_module allows importing as an encapsulated module (ala import X as Y).

  dyn_dispatch_module is a convenience for programs that want to behavior as "modules".
  These are behavior altering programs, that don't execute any code, but provide
  new code or alter behavior of builtin calls. These types of modules expect to be
  chained and to recursively call into the next module in the chain. dyn_dispatch_module
  will take the globally defined CHILD_CONTEXT and evaluate the next module in that
  context. Modules are free to alter CHILD_CONTEXT prior to calling dyn_dispatch_module.

  Modules being imported are called with callfunc set to "import" to
  allow modules to have special behavior. If the module performs some
  action on import, it is possible that dyn_* never returns, as with
  import in Python.
"""

# Initialize globals once
if callfunc == "initialize":
  # Copy our clean context for our child
  CHILD_CONTEXT = _context.copy()
  CHILD_CONTEXT["_context"] = CHILD_CONTEXT
  CHILD_CONTEXT["mycontext"] = {}

  # This cache maps a module name -> a VirtualNamespace object
  MODULE_CACHE = {}

  # This cache maps a module name -> a VirtualNamespace object for binding attributes
  MODULE_BIND_CACHE = {}

  # These extensions will be tried when looking for a module to import
  COMMON_EXTENSIONS = ["", ".py", ".repy",".py.repy", ".pp"]

  # These are the functions in the "stock" repy API,
  STOCK_API = set(["gethostname_ex","getmyip","recvmess","sendmess","openconn","waitforconn",
             "stopcomm","open","listdir","removefile","exitall","getlock","getruntime",
             "randomfloat","settimer","canceltimer","sleep","VirtualNamespace","get_thread_name",
                  "dyn_import_module","dyn_import_module_symbols","dyn_dispatch_module"])

  # Controls if we run the code preprocessor
  # If True, we will replace the old "include" directive, but this will cause a speed penalty
  RUN_PRE_PROCESS = True

#### Code Pre-processor ####

# Pre-processes the code, prior to creating the virtual namespace
def _preprocess_code(code):
  # Replace old include's
  code = _replace_include(code)

  # Return the modified code
  return code

# Replace's the old "include module.py" clause with
# dyn_import_module_symbols which should have the same effect
def _replace_include(code):
  # Find the initial include
  index = code.find("\ninclude ")
  
  # While there are more include statements, we will continue to run
  while index > -1:
    # Find the next new line
    new_line_index = code.find("\n",index+1)

    # Read the module name
    module_name = code[index+9:new_line_index]

    # Replace this occurrence with dyn_import_module_symbols
    code = code[:index+1] + "dyn_import_module_symbols('"+module_name+"', callfunc)" + code[new_line_index:]

    # Add 30 to the index, since we just added more characters
    index += 30

    # Find the next occurence of include
    index = code.find("\ninclude ",index)

  # Return the modified code
  return code



#### Helper functions ####

# Constructs a "default" context from the given context
def _default_context(import_context):
  # Construct a new context based on the importer's context
  new_context = SafeDict()
  for func in STOCK_API:
    if func in import_context:
      new_context[func] = import_context[func]

  # Add mycontext and _context
  new_context["_context"] = new_context
  new_context["mycontext"] = {}

  # Return the new context
  return new_context


# Strips the common extensions to get the actual module name
def _dy_module_name(module):
  # Strip the module name of all extensions
  for extension in COMMON_EXTENSIONS:
    module = module.replace(extension, "")
  return module


# Constructs the VirtualNamespace that is used to bind the attributes
# Caches this namespace to speed up duplicate imports
def _dy_bind_code(module, context):
  # Check if this is cached
  if module in MODULE_BIND_CACHE:
    return MODULE_BIND_CACHE[module]

  # Construct the bind code
  else:
    # Start constructing the string to form the module
    mod_str = ""

    # Check each key, and bind those we should...
    for attr in context:
      # Skip attributes starting with _ or part of the stock API
      if attr.startswith("_") or attr in STOCK_API:
        continue

      # Bind now
      mod_str += "m." + attr + " = c['" + attr + "']\n"

    # Create the namespace to do the binding
    module_bind_space = VirtualNamespace(mod_str, module+" bind-space")

    # Cache this
    MODULE_BIND_CACHE[module] = module_bind_space

    # Return the new namespace
    return module_bind_space


# Gets the code object for a module
def _dy_module_code(module):
  # Check if this module is cached
  if module in MODULE_CACHE:
    # Get the cached virtual namespace
    return MODULE_CACHE[module]

  # The module is not cached
  else:
    # Try to get a file handle to the module
    fileh = None
    for extension in COMMON_EXTENSIONS:
      try:
        fileh = open(module + extension)
        break
      except:
        pass

    # Was the file found?
    if fileh is None:
      raise Exception, "Failed to locate the module! Module: '" + module + "'"

    # Read in the code
    code = fileh.read()
    fileh.close()

    # Pre-process the code
    if RUN_PRE_PROCESS:
      code = _preprocess_code(code)

    # Create a new virtual namespace
    try:
      virt = DylinkNamespace(code,module)
    except Exception, e:
      raise Exception, "Failed to initialize the module! Got the following exception: '" + str(e) + "'"
    
    # Cache the module
    MODULE_CACHE[module] = virt

    # Return the new namespace
    return virt


# This class is used to simulate a module
class ImportedModule:
  """
  Emulates a module object. The instance field
  _context refers to the dictionary of the module,
  and _name is the name of the module.
  """
  # Initiaze the module from the context it was evaluated in
  def __init__(self, name, context):
    # Store the context and name
    self._name = name
    self._context = context

    # Get the binding namespace
    module_bind_space = _dy_bind_code(name, context)

    # Create the binding context
    module_bind_context = {"c":context,"m":self}

    # Perform the binding
    module_bind_space.evaluate(module_bind_context)

  def __str__(self):
    # Print the module name
    return "<Imported module '" + self._name + "'>"

  def __repr__(self):
    # Use the str method
    return self.__str__()


#### Main dylink Functions ####

# Main API call to link in new modules
def dylink_import_global(module, module_context,new_callfunc="import"):
  """
  <Purpose>
    Dynamically link in new modules at runtime.

  <Arguments>
    module:
            The name of a module to import. This should be excluding extensions,
            but may be the full name. e.g. for module foo.py use "foo"

    module_context: 
            The context to evaluate the module in. If you want to do a global import,
            you can evaluate in the current global context. For a bundled module,
            see dylink_import_module.

    new_callfunc:
            The value to use for callfunc during the import.
            Defaults to "import".

  <Exceptions>
    Raises an exception if the module cannot be found, or if there is a problem
    initializing a VirtualNamespace around the module. See VirtualNamespace.
  
  <Side Effects>
    module_context will likely be modified.  
  """
  # Get the actual module name
  module = _dy_module_name(module)

  # Get the code for the module
  virt = _dy_module_code(module)

  # Store the original callfunc
  orig_callfunc = (False, None)
  if "callfunc" in module_context:
    orig_callfunc = (True, module_context["callfunc"])
  
  # Set the callfunc
  module_context["callfunc"] = new_callfunc

  # Try to evaluate the module
  try:
    virt.evaluate(module_context)
  except Exception, e:
    raise Exception, "Caught exception while initializing module! Exception: '" + str(e) + "'"

  # Restore the original callfunc
  if orig_callfunc[0]:
    module_context["callfunc"] = orig_callfunc[1]



# Packages the module being imported into a module like object
def dylink_import_module(module,import_context, new_callfunc="import"):
  """
  <Purpose>
    Imports modules dynamically into a bundles module like object.

  <Arguments>
    module:
          The module to import.

    import_context:
          The context of the caller, e.g. the context of who is importing.

    new_callfunc:
          The value to use for callfunc during the import.
          Defaults to "import".

  <Exceptions>
    Raises an exception if the module cannot be found, or if there is a problem
    initializing a VirtualNamespace around the module. See VirtualNamespace. See dylink_import_global. 

  <Returns>
    A module like object.
  """
  # Get the actual module name
  module_name = _dy_module_name(module)

  # Construct a new context
  new_context = _default_context(import_context)

  # Populate the context
  dylink_import_global(module_name, new_context, new_callfunc)

  # Create a "module" object
  return ImportedModule(module_name, new_context)


#### Support for recursive modules ####

# This allows modules to recursively evaluate
def dylink_dispatch(eval_context, caller_context):
  """
  <Purpose>
    Allows a module to recursively evaluate another context.
    When the user specifies a chain of modules and programs to
    evaluate, this call steps to the next module.

  <Arguments>
    eval_context:
        The context to pass to the next module that is being evaluated.

    caller_context:
        The context of the caller.

  <Exceptions>
    As with the module being evaluated. An exception will be raised
    if the module to be evaluated cannot be initialized in a VirtualNamespace
    due to safety or syntax problems, or if the module does not exist

  <Side Effects>
    Execution will switch to the next module.

  <Returns>
    True if a recursive evaluation was performed, false otherwise.
  """
  # Check that there is a next module
  if not "callargs" in caller_context or len(caller_context["callargs"]) == 0:
    return False

  # Get the specified module
  module = caller_context["callargs"][0]

  # Get the actual module name
  module = _dy_module_name(module)

  # Get the code for the module
  virt = _dy_module_code(module)

  # Store the callfunc
  eval_context["callfunc"] = caller_context["callfunc"]
 
  # If the module's callargs is the same as the callers, shift the args by one
  if "callargs" in eval_context and eval_context["callargs"] is caller_context["callargs"]:
    eval_context["callargs"] = caller_context["callargs"][1:]
  
  # Evaluate recursively
  virt.evaluate(eval_context)

  # Return success
  return True
  

#### Dylink initializers ####

# Defines dylink as a per-context thing, and makes it available
def init_dylink(import_context, child_context):
  """
  <Purpose>
    Initializes dylink to operate in the given namespace/context.

  <Arguments>
    import_context:
            The context to initialize in.
    
    child_context:
            A copy of the import_context that is used for dyn_dispatch_module
            to pass to the child namespace.

  <Side Effects>
    dyn_* will be defined in the context.
  """

  # Define closures around dyn_* functions
  def _dyn_import_module(module,new_callfunc="import"):
    return dylink_import_module(module,import_context,new_callfunc)

  def _dyn_import_global(module,new_callfunc="import"):
    return dylink_import_global(module,import_context,new_callfunc)

  def _dylink_dispatch(eval_context=None):
    # Get the copied context if none is specified
    if eval_context is None:
      eval_context = child_context

    # Call dylink_dispatch with the proper eval context
    return dylink_dispatch(eval_context,import_context)


  # Make these available
  import_context["dyn_import_module"] = _dyn_import_module
  import_context["dyn_import_module_symbols"] = _dyn_import_global
  import_context["dyn_dispatch_module"] = _dylink_dispatch


# Wrap around VirtualNamespace
class DylinkNamespace(object):
  """
  Wraps a normal namespace object to automatically update the context
  so that dylink_* operates correctly.
  """
  # Take any arguments, pass it down
  def __init__(self,*args,**kwargs):
    # Construct the underlying virtual namespace
    self._virt = VirtualNamespace(*args,**kwargs)

    # Set the last eval context to None
    self._eval_context = None

  # Handle evaluate
  def evaluate(self,context,enable_dylink=True):
    # Convert context to a SafeDict if it isn't one
    if type(context) is dict:
      context = SafeDict(context)
    
    # Explicitly remove dylink_* calls if disabled
    if not enable_dylink:
      calls = ["dyn_import_module","dyn_import_module_symbols","dyn_dispatch_module"]
      for call in calls:
        if call in context:
          del context[call]

    # Copy the context if this is the first evaluate of this context
    if enable_dylink and context is not self._eval_context:
      # Copy the context before evaluation
      child_context = context.copy()
      child_context["_context"] = child_context
      child_context["mycontext"] = {}

      # Let the module see this copy
      context["CHILD_CONTEXT"] = child_context

      # Initialize the context to use dylink
      init_dylink(context,child_context)

    # Inform the module if dylink is available
    context["HAS_DYLINK"] = enable_dylink

    # Set this as the last evaluated context
    self._eval_context = context

    # Evaluate
    self._virt.evaluate(context)

    # Return the context
    return context
    

# Functional wrapper around DylinkNamespace
def get_DylinkNamespace(*args,**kwargs):
  return DylinkNamespace(*args,**kwargs)

#### Call into the next module ####

# Update the child context
if callfunc == "initialize":
  CHILD_CONTEXT["VirtualNamespace"] = get_DylinkNamespace

# Evaluate the next module
dylink_dispatch(CHILD_CONTEXT, _context)

