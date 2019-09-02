# Finite state machine class for AppDaemon (Home Assistant).

from urllib.parse import quote
import datetime

class Fsm:
  # Finite state machine implementation for AppDaemon and Home Assistant

  # Helper function to simplify print and log messages
  def prefix(self):
    return '{} : '.format(self.id)
  
  def __init__(self, hass, id='', states=None, entity=None, health_entity=None):
    # - id is optional but useful for debugging
    # - states is a required list of; State objects
    # - entity is an optional hass entity where the current state is published
    # - entity is an optional  hass entity where the health of this fsm is made public
    
    self.hass = hass
    self.id = id
    self.states = states
    self.entity = entity
    self.health_entity = health_entity

    self.state = None
    self.alive_handle = None
    
    self.update_health("Init")
      
    self.states_dict = {}
    for state in self.states:
      self.hass.log('{}State : {}'.format(self.prefix(), state.id), level='INFO')
      self.states_dict[state.id] = state
    
    if self.entity:
      # Try loading the state from Home Assistant.
      entity_state = self.hass.get_state(self.entity)
      assert entity_state, ('Entity not found: {} {} {}'.format(__name__, self.id, self.entity))
      
      if entity_state in {state.id for key,state in self.states_dict.items()}:
        self.state = self.states_dict[entity_state]
      else:
        self.hass.log('{}Unrecognized state: {}'.format(self.prefix(), entity_state), level='WARNING')

      # Listen for state changes initiated in Home Assistant.
      temp = self.hass.get_state(self.entity)
      assert temp, ('Entity not found: {} {} {}'.format(__name__, self.id, self.entity))
      
      self.hass.log('{}Added listen_state <{}> <{}>'.format(self.prefix(), self.entity, self.external_state_callback), level='INFO')
      self.hass.listen_state(self.external_state_callback, self.entity)

    if not self.state:
      self.state = list(states)[0]
      self.hass.log('{}Initial state unset - using {}'.format(self.prefix(), self.state.id), level='INFO')

#    self.hass.log('{}Initializing'.format(self.prefix()), level='INFO')
    for index, state in enumerate(self.states):
      state.initialize(self.hass, self, index)
#    self.hass.log('{}Initializing DONE'.format(self.prefix()), level='INFO')
      
    self.hass.log('{} initial state set to {}'.format(self.prefix(), self.state.id), level='INFO')
    self.change_state(self.state)
    self.state.activate()

    self.alive_handle = self.hass.run_every(self.alive_callback, datetime.datetime.now(), 60)

    self.update_health("Init done")


  def update_health(self, condition, stop=None):
    self.health = condition
    if self.health_entity:
      text = "{} {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), self.health)
      self.hass.set_state(self.health_entity, state=text)

    if stop == True:
      # Stop alive timer
      if self.alive_handle:
        self.hass.cancel_timer(self.alive_handle)
        self.alive_handle = None

  # Function to find an object with certain id
  def find_state(self, state_name):
    if state_name in self.states_dict:
      return self.states_dict[state_name]
    else:
      self.hass.log('{}find_state cannot find {}'.format(self.prefix(), state_name), level='ERROR')
      return None


  def change_state(self, state):
    self.state = state
    if self.entity:
      self.hass.set_state(self.entity, state=self.state.name)

  # Call check when something happened
  def check(self):
    self.hass.log('{}check'.format(self.prefix()), level='INFO')

    
  def external_state_callback(self, entity, attribute, old, new, kwargs):
    if self.state.id != new:
      self.hass.log('{}Fsm state change (from hass) state={} old={} new={}'.format(self.prefix(), self.state.id, old, new), level='INFO')


  def alive_callback(self, kwargs):
    if self.health_entity:
      self.update_health("Alive")
    
      
  # Helper function to get the dot-format representation of this object
  def get_dot(self):
    dot = ''
    dot += 'label = ' + self.id + ';\n'
    dot += 'labelloc = "t";\n'

    for state in self.states:
      state_label = state.id
      
    for state in self.states:
      dot += state.get_dot() + '\n'
    return 'digraph "' + self.id + '" {{{}}}'.format(dot)


  def log_graph_link(self):
#    link = 'https://stamm-wilbrandt.de/GraphvizFiddle/#{}'.format(
#      quote(self.get_dot()))

    link = 'https://stamm-wilbrandt.de/GraphvizFiddle/2.1.2/#{}'.format(
      quote(self.get_dot()))

#    link = 'https://dreampuf.github.io/GraphvizOnline/#{}'.format(
#        quote(self.get_dot()))
    self.hass.log('{}Transition graph: {}'.format(self.prefix(), link))
    self.hass.log('{}Transition graph2: {}'.format(self.prefix(), self.get_dot()))
    

class State:
  # Helper function to simplify print and log messages
  def prefix(self):
    return '{}_{} : '.format(self.fsm.id, self.id)
  
  def __init__(self, id=None, name=None, transitions=None, enter_programs=None, exit_programs=None):
    # - id is optional but useful for debugging
    # - name is the name of this state. If set to None, it will use id instead
    # - transitions is a list of; Transition objects
    # - enter_programs is an optional list of; objects containing a 'program' function, or a python string to be executed
    # - exit_programs is an optional list of; objects containing a 'program' function, or a python string to be executed
    
    self.id = id
    self.name = name
    self.enter_programs = enter_programs
    self.exit_programs = exit_programs
    self.transitions = transitions

    if self.name == None:
      self.name = self.id
    
  def initialize(self, hass, fsm, index):
    try:
      self.hass = hass
      self.fsm = fsm
      self.index = index

      if not self.id:
        self.id = '{}_s{}'.format(self.fsm.id, index)
      else:
        self.id = '{}_{}'.format(self.fsm.id, self.id)
      
      
      if self.transitions:
        for index, transition in enumerate(self.transitions):
          transition.initialize(self.hass, self, index)
          transition.add_callback(self.transition_callback)

    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)


  def activate(self):
    try:
      if self.transitions:
        for transition in self.transitions:
          transition.activate()
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)
      

  # Enter is called when the state machine decides to enter this state
  def enter(self):
    try:
      # Called when the fsm changes state
      assert self.fsm, ('{} : State not initialized'.format(self.id))
      #    self.hass.log('{}enter'.format(self.prefix(), level='INFO'))
      self.fsm.change_state(self)

      if self.enter_programs:
        for enter_program in self.enter_programs:
          if type(enter_program) == str:
            exec(enter_program)
          else:
            enter_program.program(self)
      self.activate()
      
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)

          
  # Exit is called when the state machine decides to exit this state
  def exit(self):
    try:
      #    self.hass.log('{}exit'.format(self.prefix()), level='INFO')
      if self.transitions:
        for transition in self.transitions:
          transition.deactivate()
      
          if self.exit_programs:
            for exit_program in self.exit_programs:
              exit_program.program(self)
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)

        
  # Call check when something happened. If all conditions for a transition are true, it will be activated
  def check(self):
    try:
      if self.fsm.state != self:
        raise "Error wtf: {} {} {}".format(__name__, self.id, e)
     
      if self.transitions:
        for transition in self.transitions:
          #      self.hass.log('{}check {} = {}'.format(self.prefix(), transition.id, transition.status), level='INFO')
          if transition.status:
            transition.execute()
            break
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)
            

          
  # Callback when status for a transition has changed
  def transition_callback(self):
    try:
      # self.hass.log('{}transition_callback'.format(self.prefix()), level='INFO')
      if self.fsm.state == self:
        self.check()
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)

      
  # Helper function to get the dot-format representation of this object
  def get_dot(self):
    dot = ''

    label = self.id
    
    if self.enter_programs:
      label += '\\n [enter_programs: '
      for enter_program in self.enter_programs:
        if type(enter_program) == str:
          label += enter_program[:20]
        else:
          label += enter_program.__name__ + ' '
      label += ']'

    if self.exit_programs:
      label += '\\n [exit_programs: '
      for exit_program in self.exit_programs:
        label += exit_program.__name__ + ' '
      label += ']'
      
    dot += '"' + self.id + '" [label="' + label + '" labelfloat=true]\n'
    
    if self.transitions:
      for transition in self.transitions:
        dot += transition.get_dot()
    return dot

  
class Eq:
  # This is a class used as operator for a Condition object. Will check against required operand
  def check(self):
    assert self.operand, ('{} : missing operand'.format(self.id)) 
    status = self.entity_state == self.operand
    return status

  # Helper function to get the dot-format representation of this object
  def get_dot(self):
    return "=='" + self.operand + "'"

  
class Neq:
  # This is a class used as operator for a Condition object. Will check against required operand
  def check(self):
    assert self.operand, ('{} : missing operand'.format(self.id)) 
    status = self.entity_state != self.operand
    return status

  # Helper function to get the dot-format representation of this object
  def get_dot(self):
    return "!='" + self.operand + "'"

  
class LT:
  # This is a class used as operator for a Condition object. Will check against required operand
  def check(self):
    assert self.operand, ('{} : missing operand'.format(self.id)) 
    status = float(self.entity_state) < float(self.operand)
    return status

  # Helper function to get the dot-format representation of this object
  def get_dot(self):
    return "<'" + self.operand + "'"

class LE:
  # This is a class used as operator for a Condition object. Will check against required operand
  def check(self):
    assert self.operand, ('{} : missing operand'.format(self.id)) 
    status = float(self.entity_state) <= float(self.operand)
    return status

  # Helper function to get the dot-format representation of this object
  def get_dot(self):
    return "<='" + self.operand + "'"

class GT:
  # This is a class used as operator for a Condition object. Will check against required operand
  def check(self):
    assert self.operand, ('{} : missing operand'.format(self.id)) 
    status = float(self.entity_state) > float(self.operand)
    return status

  # Helper function to get the dot-format representation of this object
  def get_dot(self):
    return ">'" + self.operand + "'"

class GE:
  # This is a class used as operator for a Condition object. Will check against required operand
  def check(self):
    assert self.operand, ('{} : missing operand'.format(self.id)) 
    status = float(self.entity_state) >= float(self.operand)
    return status

  # Helper function to get the dot-format representation of this object
  def get_dot(self):
    return ">='" + self.operand + "'"

  
class Transition:
  # Helper function to simplify print and log messages
  def prefix(self):
    return '{} : '.format(self.id)
  
  def __init__(self, id=None, next='', conditions=None, programs=None):
    # - id is optional but useful for debugging
    # - next is the id of the next state if all conditions are found true
    # - conditions is a list of; Condition objects
    # - programs is an optional object containing a list of program functions

    # status will always reflect the status of this condition and is intended to be probed from outside
    self.status = self.last_status = None
    self.id = id
    self.conditions = conditions
    self.next_state_name = next
    self.programs = programs


      
  def initialize(self, hass, state, index):
    self.hass = hass
    self.callbacks = []
    self.state = state
    self.index = index

    if not self.id:
      self.id = '{}_t{}'.format(self.state.id, index)
      
    self.next_state = self.state.fsm.find_state(self.next_state_name)

    #    self.hass.log('{}Initializing'.format(self.prefix()), level='INFO')
    for index, condition in enumerate(self.conditions):
      condition.initialize(self.hass, self, index)
      condition.add_callback(self.condition_callback)
    self.update_status()
    #    self.hass.log('{}Initializing done'.format(self.prefix()), level='INFO')

    #    self.hass.log('{}Initial status={}'.format(self.prefix(), self.status, level='INFO'))

  def deactivate(self):
    for condition in self.conditions:
      #      self.hass.log('{}deactivate {}'.format(self.prefix(), condition.id), level='INFO')
      condition.deactivate()
    self.status = self.last_status = None

  def activate(self):
    self.status = self.last_status = None
    for condition in self.conditions:
      condition.activate()
    self.check()

      
  def update_status(self):
    self.status = True
    for condition in self.conditions:
      if condition.status != True:
        self.status = False
    

  # Call check when something happened. If the status changes, all subscribing listeners will have their callback called  
  def check(self):
    self.update_status()
    
    if self.status != self.last_status:
      for callback in self.callbacks:
        callback()
    self.last_status = self.status

  def execute(self):
    self.hass.log('{}Started in <{}> used <{}> to get to <{}>'.format(self.prefix(), self.state.id, self.id, self.next_state_name), level='INFO')
    
    # Exit state
    self.state.exit()
    
    # Transition programs
    if self.programs:
      for program in self.programs:
        program.program(self)

    # Enter state
    assert self.next_state, ('Next state not set: {} {} {}'.format(__name__, self.id, self.next_state))
    self.next_state.enter()


  # Callback when status for a condition has changed
  def condition_callback(self):
    # self.hass.log('{}condition_callback'.format(self.prefix()), level='INFO')
    self.check()

  def add_callback(self, callback):
    self.callbacks.append(callback)
    
  # Helper function to get the dot-format representation of this object
  def get_dot(self):
    condition_nbr = 0
    sub_dot = ''
    for condition in self.conditions:
      condition_nbr += 1
      if condition_nbr > 1:
        sub_dot += ' &&\n'
      if len(self.conditions) > 1:
        sub_dot += '('
      sub_dot += condition.get_dot()
      if len(self.conditions) > 1:
        sub_dot += ')'
      
    label = self.id
    if self.programs:
      for program in self.programs:
        label += '\\n [program: ' + program.__name__ + ']'

    dot = '"{}"->"{}"[label="{}\\n {}"];'.format(self.state.id, self.next_state.id, label, sub_dot)
    return dot

  
class Condition:
  # Helper function to simplify print and log messages
  def prefix(self):
    return '{} : '.format(self.id)
  
  def __init__(self, id=None, entity=None, attribute=None, operator=Eq, operand=None, stability_time=None, timeout_time=None, timeout_entity=None, years=None, months=None, weeks=None, days=None, weekdays=None, hours=None, minutes=None):
    # - id is optional but useful for debugging
    # - entity is an optional hass entity which can be tested by the operator
    # - attribute is an optional hass attribute for entity which can be tested by the operator
    # - operator is required if entity is used, and is an object with a check function
    # - stability_time is optional but only used if entity is used, and sets a minimum time operator must be true before this condition evaluates as true
    # - timeout_time is optional and a minimum time before this condition evaluates as true
    # - timeout_entity is optional and name of entity containing a minimum time before this condition evaluates as true
    # - years, months, weeks, days, weekdays, hours, minutes are lists of allowed times. If more than one is set, consider an implicit "and" between them

    # status will always reflect the status of this condition and is intended to be probed from outside
    self.status = self.last_status = None

    self.id = id
    self.entity = entity
    self.attribute = attribute
    self.operator = operator
    self.operand = operand
    self.stability_time = stability_time
    self.timeout_time1 = timeout_time
    self.timeout_entity = timeout_entity

    self.years = years
    self.months = months
    self.weeks = weeks
    self.days = days
    self.weekdays = weekdays
    self.hours = hours
    self.minutes = minutes

     
  def initialize(self, hass, transition, index):
    try:
      self.hass = hass
      self.transition = transition
      self.index = index
  
      if not self.id:
        self.id = '{}_c{}'.format(self.transition.id, index)
      
      self.callbacks = []
  
      self.entity_status = False
  
      self.timeout_status = False
      self.timer_handle = None
  
      self.stability_status = False
      self.stability_handle = None
  
      self.time_handle = None
      self.update_time_status()
  
      if self.entity == None or self.operator == None:
        #      self.hass.log('{}State is disabled'.format(self.prefix()), level='INFO')
        self.entity_status = True
        self.stability_status = True
      else:
        temp = self.hass.get_state(self.entity)
        assert temp, ('Entity not found: {} {} {}'.format(__name__, self.id, self.entity))
  
        if self.attribute != None:
          self.hass.log('{}Added listen_state entity={} attribute={} callback={}'.format(self.prefix(), self.entity, self.attribute, self.condition_state_callback), level='INFO')
          kwargs = "attribute='" + self.attribute + "'"
          self.hass.listen_state(self.condition_state_callback, self.entity, attribute=self.attribute)
          entity_state = self.hass.get_state(self.entity, attribute=self.attribute)
          assert entity_state, ('Entity not found: {} {} {}'.format(__name__, self.id, self.entity))
        else:
          self.hass.log('{}Added listen_state entity={} callback={}'.format(self.prefix(), self.entity, self.condition_state_callback), level='INFO')
          self.hass.listen_state(self.condition_state_callback, self.entity)
          entity_state = self.hass.get_state(self.entity)
          assert entity_state, ('Entity not found: {} {} {}'.format(__name__, self.id, self.entity))
          
        self.condition_state_change(entity_state)
  
      self.timeout_time2 = None
      if self.timeout_entity:
        temp = self.hass.get_state(self.timeout_entity)
        assert temp, ('Entity not found: {} {} {}'.format(__name__, self.id, self.entity))

        self.hass.listen_state(self.timeout_state_callback, self.timeout_entity)
        timeout_state = self.hass.get_state(self.timeout_entity)
        assert timeout_state, ('Entity not found: {} {} {}'.format(__name__, self.id, self.entity))
        
        self.timeout_time2 = float()
        self.hass.log('{}Timeout_entity {} with value {}'.format(self.prefix(), self.timeout_entity, self.timeout_time2), level='INFO')
  
        
      self.update_status()
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)
      


  # Callback if the entity containing the timeout_time changes
  def timeout_state_callback(self, entity, attribute, old, new, kwargs):
    try:
      self.timeout_time2 = float(new)
      self.hass.log('{}Timeout state changed to <{}>'.format(self.prefix(), self.timeout_time2), level='INFO')
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)


  def update_time_status(self):
    try:
      self.hass.log('{}update_time_status'.format(self.prefix(), level='INFO'))
      
      if self.years is None and self.months is None and self.weeks is None and self.days is None and self.weekdays is None and self.hours is None and self.minutes is None:
        self.time_status = True
      else:
        if self.time_handle == None:
          callback_time = datetime.datetime.now()
        
          callback_time = callback_time.replace(microsecond=0)
          callback_time = callback_time.replace(second=0) + datetime.timedelta(minutes=1)
          callback_interval = 60
          if self.minutes == None:
            callback_time = callback_time.replace(minute=0) + datetime.timedelta(hours=1)
            callback_interval = 3600
            if self.hours == None:
              callback_time = callback_time.replace(hour=0) + datetime.timedelta(days=1)
              callback_interval = 24*3600
            
          self.hass.log('{}callback: {} every {}'.format(self.prefix(), callback_time, callback_interval), level='INFO')
          self.time_handle = self.hass.run_every(self.time_callback, callback_time, callback_interval)
      
        now = datetime.datetime.now()
        self.time_status = ( (not self.years or now.year in self.years) and
                             (not self.months or now.month in self.months) and
                             (not self.days or now.day in self.days) and
                             (not self.hours or now.hour in self.hours) and
                             (not self.minutes or now.minute in self.minutes) and
                             (not self.weeks or now.isocalendar()[1] in self.weeks) and
                             (not self.weekdays or now.weekday in self.weekdays) )
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)

      
  def time_callback(self, kwargs):
    try:
      self.hass.log('{}time_callback'.format(self.prefix(), level='INFO'))

      self.update_time_status()
      self.check()
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)
      
   
  def condition_state_callback(self, entity, attribute, old, new, kwargs):
    try:
      self.hass.log('{}Condition state changed from <{}> to <{}>'.format(self.prefix(), old, new), level='INFO')
      self.condition_state_change(new)
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)
      

  def condition_state_change(self, new):
    try:
      self.entity_state = new
      
      self.entity_status = self.operator.check(self)

      if self.entity_status:
        if self.stability_time:
          if self.stability_handle == None:
            #        self.hass.log('{}activate stability {}s'.format(self.prefix(), self.stability_time), level='INFO')
            self.stability_handle = self.hass.run_in(self.stability_callback, self.stability_time)
            self.stability_status = False
        else:
          #      self.hass.log('{}Stability is disabled'.format(self.prefix()), level='INFO')
          self.stability_status = True
      else:
        if self.stability_time != None:
          if self.stability_handle != None:
            #      self.hass.log('{}deactivate stability'.format(self.prefix()), level='INFO')
            self.hass.cancel_timer(self.stability_handle)
            self.stability_handle = None
            self.stability_status = False
        else:
          self.stability_status = True
          
      self.check()
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)
    

  # Deactivate
  def deactivate(self):
    try:
      #    self.hass.log('{}deactivate'.format(self.prefix()), level='INFO')
      if self.timer_handle != None:
        #      self.hass.log('{}cancel timer'.format(self.prefix()), level='INFO')
        self.hass.cancel_timer(self.timer_handle)
        self.timer_handle = None
      self.timeout_status = False
  
      self.status = self.last_status = None
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)
       
  # Activate
  def activate(self):
    try:
      #      self.hass.log('{}activate'.format(self.prefix()), level='INFO')
      if self.timeout_time1!=None or self.timeout_time2!=None:
        timeout_time = 0
        if self.timeout_time1:
          timeout_time = timeout_time + self.timeout_time1
        if self.timeout_time2:
          timeout_time = timeout_time + self.timeout_time2
          
        if self.timer_handle == None:
          self.hass.log('{}activate timer {}s'.format(self.prefix(), timeout_time), level='INFO')
          self.timer_handle = self.hass.run_in(self.timer_callback, timeout_time)
          self.timeout_status = False
        else:
          self.hass.log('{}activate timer - already active?!'.format(self.prefix()), level='ERROR')
        
      else:
        #      self.hass.log('{}Timeout is disabled'.format(self.prefix()), level='INFO')
        self.timeout_status = True
  
      self.check()
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)
      
      
  # This is the callback function when timeout timer expires
  def timer_callback(self, kwargs):
    try:
      self.hass.log('{}Timer callback'.format(self.prefix()), level='INFO')
      self.timeout_status = True
      self.timer_handle = None
      self.check()
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)
    

  # This is the callback function when stability timer expires
  def stability_callback(self, kwargs):
    try:
      self.hass.log('{}Stability callback'.format(self.prefix()), level='INFO')
      self.stability_status = True
      self.stability_handle = None
      self.check()
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)


  # Will update status of this condition
  def update_status(self):
    try:
      self.status = self.timeout_status and self.entity_status and self.stability_status and self.time_status
      self.hass.log('{}Check timeout/state/stability/time = {}/{}/{}/{} = {}'.format(self.prefix(), self.timeout_status, self.entity_status, self.stability_status, self.time_status, self.status), level='INFO')
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)
    

  # Call check when something happened. If the status changes, all subscribing listeners will have their callback called  
  def check(self):
    try:
      self.update_status()
      
      if not self.last_status == self.status:
        # Announce to listeners
        for callback in self.callbacks:
          callback()
  
      self.last_status = self.status
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)

  # Function called from super object to register a callback function
  def add_callback(self, callback):
    try:
      self.callbacks.append(callback)
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)
      

  # Helper function to get the dot-format representation of this object
  def get_dot(self):
    try:
      dot = ''
      if self.entity != None:
        dot += self.entity + self.operator.get_dot(self)
        # operator=None, stability_time=None
      if self.timeout_time1 != None:
        dot += '#' + str(self.timeout_time1) + 's'
      if self.timeout_time2 != None:
        dot += '#' + str(self.timeout_time2) + 's'
      return dot
    except Exception as e:
      raise "Error: {} {} {}".format(__name__, self.id, e)
        
