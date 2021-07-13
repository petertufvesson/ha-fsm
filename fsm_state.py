# Finite state machine class for AppDaemon (Home Assistant).

from datetime import datetime, timedelta

import fsm_fsm

debug = False

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
      assert hass is not None
      assert fsm is not None
      assert index is not None
      
      self.hass = hass
      self.fsm = fsm
      self.index = index

      if not self.id:
        self.id = '{}_s{}'.format(self.fsm.id, index)
      else:
        self.id = '{}_{}'.format(self.fsm.id, self.id)
      
      
      if self.transitions:
          for index, transition in enumerate(self.transitions):
              if debug: self.hass.log('{} transitions {} = {}'.format(self.prefix(), index, transition), level='ERROR')
              
              transition.initialize(self.hass, self, index)
              transition.add_callback(self.transition_callback)

    except Exception as e:
      self.hass.log('{}State created with exception e={}'.format(self.prefix(), e))
#      raise ValueError("State initialize Error: name={} id={} e={}".format(__name__, self.id, e))


  def activate(self):
    try:
      if self.transitions:
        for transition in self.transitions:
          transition.activate()
    except Exception as e:
      raise ValueError("State activate Error: name={} id={} e={}".format(__name__, self.id, e))
      

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
      self.hass.log("State enter Error: name={} id={} e={}".format(__name__, self.id, e), level='INFO')

          
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
      raise ValueError("State exit Error: name={} id={} e={}".format(__name__, self.id, e))

        
  # Call check when something happened. If all conditions for a transition are true, it will be activated
  def check(self):
      if debug: self.hass.log('{}check'.format(self.prefix()), level='ERROR')
      try:
          if self.fsm.state != self:
              raise ValueError("State check1 Error: name={} id={} e={}".format(__name__, self.id, e))
     
          if self.transitions:
              if debug: self.hass.log('{}checking transitions = {}'.format(self.prefix(), len(self.transitions)), level='ERROR')
              for transition in self.transitions:
                  if debug: self.hass.log('{}check {} = {}'.format(self.prefix(), transition.id, transition.status), level='INFO')
                  if transition.status:
                      transition.execute()
                      break
      except Exception as e:
          raise ValueError("State check2 Error: name={} id={} e={}".format(__name__, self.id, e))
           

          
  # Callback when status for a transition has changed
  def transition_callback(self):
      try:
          if debug: self.hass.log('{}transition_callback'.format(self.prefix()), level='INFO')
          if self.fsm.state == self:
              self.check()
      except Exception as e:
          raise ValueError("State callback Error: name={} id={} e={}".format(__name__, self.id, e))

      
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

  
