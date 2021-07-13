
from datetime import datetime, timedelta

debug = False

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

    assert isinstance(conditions, (list, type(None)))
    self.conditions = conditions
    self.next_state_name = next

    assert isinstance(programs, (list, type(None)))
    self.programs = programs

      
  def initialize(self, hass, state, index):
    assert hass is not None

    self.hass = hass
    self.callbacks = []
    self.state = state
    self.index = index

    try:
      if not self.id:
        self.id = '{}_t{}'.format(self.state.id, index)
      
      self.next_state = self.state.fsm.find_state(self.next_state_name)

      #      self.hass.log('{}Initializing'.format(self.prefix()), level='INFO')
      for index, condition in enumerate(self.conditions):
        condition.initialize(self.hass, self, index)
        condition.add_callback(self.condition_callback)
      self.update_status()
      #      self.hass.log('{}Initializing done'.format(self.prefix()), level='INFO')

      #    self.hass.log('{}Initial status={}'.format(self.prefix(), self.status, level='INFO'))
    except Exception as e:
      raise ValueError("Transition initialize Error: name={} id={} e={}".format(__name__, self.id, e))

    
  def deactivate(self):
      if self.conditions != None:
          for condition in self.conditions:
              #      self.hass.log('{}deactivate {}'.format(self.prefix(), condition.id), level='INFO')
              condition.deactivate()
              self.status = self.last_status = None

              
  def activate(self):
      self.status = self.last_status = None
      for condition in self.conditions:
          #          self.hass.log('{}activate {}'.format(self.prefix(), condition.id), level='INFO')
          condition.activate()
      self.check()

      
  def update_status(self):
      #    self.hass.log('{}update_status'.format(self.prefix()), level='ERROR')
      self.status = True
      for condition in self.conditions:
          if condition.status != True:
              self.status = False
    

  # Call check when something happened. If the status changes, all subscribing listeners will have their callback called  
  def check(self):
    if debug: self.hass.log('{}check'.format(self.prefix()), level='ERROR')
    self.update_status()
    if debug: self.hass.log('{}check from {} to {}'.format(self.prefix(), self.last_status, self.status), level='ERROR')
    
    if self.status != self.last_status:
      if debug: self.hass.log('{}status changed from {} to {}'.format(self.prefix(), self.last_status, self.status), level='ERROR')
      try:
        self.callbacks
      except Exception as e:
        self.hass.log('{} has no callbacks'.format(self.prefix()), level='ERROR')
      if self.callbacks != []:
        for callback in self.callbacks:
          if debug: self.hass.log('{}  ..{}'.format(self.prefix(), callback), level='ERROR')
          callback()
      self.last_status = self.status

  def execute(self):
      if debug: self.hass.log('{}Started in <{}> used <{}> to get to <{}>'.format(self.prefix(), self.state.id, self.id, self.next_state_name), level='INFO')
    
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
#  def condition_callback(self):
  def condition_callback(self, kwargs):
      if debug: self.hass.log('{}condition_callback'.format(self.prefix()), level='ERROR')
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

