# Finite state machine class for AppDaemon (Home Assistant).

from datetime import datetime, timedelta

debug = False

def enabled_state_transform(state):
  if state == "on":
    return True
  else:
    return False


class TRUE2:
  # This is a class used as operator for a Condition object. Will always be true
  def check(self):
    if debug: self.hass.log('{}check'.format(self.prefix()), level='INFO')
    status = True
    return status

  # Helper function to get the dot-format representation of this object
  def get_dot(self):
    return "TRUE"


class Eq:
  # This is a class used as operator for a Condition object. Will check against required operand
  def check(self):
    if debug: self.hass.log('{}check'.format(self.prefix()), level='INFO')
    assert self.operand, ('{} : missing operand'.format(self.id))
    try:
      status = self.entity_state == self.operand
    except Exception as e:
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))
    return status

  # Helper function to get the dot-format representation of this object
  def get_dot(self):
    return "=='" + str(self.operand) + "'"

  
class Neq:
  # This is a class used as operator for a Condition object. Will check against required operand
  def check(self):
    assert self.operand, ('{} : missing operand'.format(self.id))
    try:
      status = self.entity_state != self.operand
    except Exception as e:
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))
    return status

  # Helper function to get the dot-format representation of this object
  def get_dot(self):
    return "!='" + str(self.operand) + "'"

  
class LT:
  # This is a class used as operator for a Condition object. Will check against required operand
  def check(self):
    assert self.operand, ('{} : missing operand'.format(self.id))
    try:
      status = float(self.entity_state) < float(self.operand)
    except Exception as e:
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))
    return status

  # Helper function to get the dot-format representation of this object
  def get_dot(self):
    return "<'" + str(self.operand) + "'"

class LE:
  # This is a class used as operator for a Condition object. Will check against required operand
  def check(self):
    assert self.operand, ('{} : missing operand'.format(self.id))
    try:
      status = float(self.entity_state) <= float(self.operand)
    except Exception as e:
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))
    return status

  # Helper function to get the dot-format representation of this object
  def get_dot(self):
    return "<='" + str(self.operand) + "'"

class GT:
  # This is a class used as operator for a Condition object. Will check against required operand
  def check(self):
    assert self.operand, ('{} : missing operand'.format(self.id))
    try:
      status = float(self.entity_state) > float(self.operand)
    except Exception as e:
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))
    return status

  # Helper function to get the dot-format representation of this object
  def get_dot(self):
    return ">'" + str(self.operand) + "'"

class GE:
  # This is a class used as operator for a Condition object. Will check against required operand
  def check(self):
    assert self.operand, ('{} : missing operand'.format(self.id))
    try:
      status = float(self.entity_state) >= float(self.operand)
      self.hass.log('{} GE {} >= {} is {}'.format(self.prefix(), float(self.entity_state), float(self.operand), status), level='INFO')
    except Exception as e:
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))
    return status

  # Helper function to get the dot-format representation of this object
  def get_dot(self):
    return ">='" + str(self.operand) + "'"

  
class Condition:
  # Helper function to simplify print and log messages
  def prefix(self):
    return '{} : '.format(self.id)
  
  def __init__(self, id=None, enabled=True, enabled_entity=None, entity=None, attribute=None, operator=Eq, operand=None, only_posedge=False, stability_time=None, timeout_time=None, timeout_entity=None, years=None, months=None, weeks=None, days=None, weekdays=None, hours=None, minutes=None):
    # - id is optional but useful for debugging
    # - enabled tells if this Condition is enabled ((default) or not
    # - enabled_entity is an optional name of entity to tell if this Condition is enabled or not
    # - entity is an optional hass entity which can be tested by the operator
    # - attribute is an optional hass attribute for entity which can be tested by the operator
    # - operator is required if entity is used, and is an object with a check function
    # - operand is the operand for the operator above
    # - only_posedge can be set to True if the condition should only be evaluated just when the entity changes value from False to True
    # - stability_time is optional but only used if entity is used, and sets a minimum time operator must be true before this condition evaluates as true
    # - timeout_time is optional and a minimum time before this condition evaluates as true
    # - timeout_entity is optional and name of entity containing a minimum time before this condition evaluates as true
    # - years, months, weeks, days, weekdays, hours, minutes are lists of allowed times. If more than one is set, consider an implicit "and" between them

    # status will always reflect the status of this condition and is intended to be probed from outside
    self.status = self.last_status = None
    
    self.id = id

    assert isinstance(enabled, (bool, type(None)))
    self.enabled = enabled
    self.enabled_entity = enabled_entity
    self.enabled_state = True # ??
    self.entity = entity
    self.attribute = attribute
    self.operator = operator
    self.operand = operand
    self.only_posedge = only_posedge
    self.stability_time = stability_time
    self.timeout_time1 = timeout_time
    self.timeout_entity = timeout_entity

    assert isinstance(years, (list, range, type(None)))
    self.years = years

    assert isinstance(months, (list, range, type(None)))
    self.months = months

    assert isinstance(weeks, (list, range, type(None)))
    self.weeks = weeks

    assert isinstance(days, (list, range, type(None)))
    self.days = days

    assert isinstance(weekdays, (list, range, type(None)))
    self.weekdays = weekdays

    assert isinstance(hours, (list, range, type(None))), "hours cannot be of type {}".format(type(hours))
    self.hours = hours

    assert isinstance(minutes, (list, range, type(None)))
    self.minutes = minutes

    self.callbacks = []
  
    self.entity_status = False
  
    self.timeout_status = False
    self.timer_handle = None
      
    self.stability_status = False
    self.stability_handle = None
  
    self.time_handle = None

    self.timeout_time2 = None

    
  def initialize(self, hass, transition, index):
    try:
      self.hass = hass
      self.transition = transition
      self.index = index
  
      if not self.id:
        self.id = '{}_c{}'.format(self.transition.id, index)
      
      if debug: self.hass.log('{}Condition inititilizing'.format(self.prefix()), level='INFO')

      self.update_time_status()
  
      if self.entity == None or self.operator == None:
        if debug: self.hass.log('{}State is disabled'.format(self.prefix()), level='INFO')
        self.entity_status = True
        self.stability_status = True
      else:
        try:
          temp = self.try_get_state(self.entity)
        except Exception as e:
          raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))
         
        assert temp, ('Entity not found: {} {} {}'.format(__name__, self.id, self.entity))
  
        if self.attribute != None:
          #          self.hass.log('{}Added listen_state entity={} attribute={} callback={}'.format(self.prefix(), self.entity, self.attribute, self.condition_state_callback), level='INFO')
          kwargs = "attribute='" + self.attribute + "'"
          self.hass.listen_state(self.condition_state_callback, self.entity, attribute=self.attribute)
          entity_state = self.hass.get_state(self.entity, attribute=self.attribute)
          assert entity_state, ('Entity not found: {} {} {}'.format(__name__, self.id, self.entity))
        else:
          #          self.hass.log('{}Added listen_state entity={} callback={}'.format(self.prefix(), self.entity, self.condition_state_callback), level='INFO')
          self.hass.listen_state(self.condition_state_callback, self.entity)
          entity_state = self.try_get_state(self.entity)
          assert entity_state, ('Entity not found: {} {} {}'.format(__name__, self.id, self.entity))
          
        self.condition_state_change(entity_state)
  
      if self.timeout_entity:
        temp = self.try_get_state(self.timeout_entity)
        assert temp, ('Entity not found: {} {} {}'.format(__name__, self.id, self.entity))

        self.hass.listen_state(self.timeout_state_callback, self.timeout_entity)
        timeout_state = self.try_get_state(self.timeout_entity)
        assert timeout_state, ('Entity not found: {} {} {}'.format(__name__, self.id, self.entity))
        
        self.timeout_time2 = float(timeout_state)
#        self.hass.log('{}Timeout_entity {} with value {}'.format(self.prefix(), self.timeout_entity, self.timeout_time2), level='INFO')
  
        
      if self.enabled_entity:
        #        temp = self.try_get_state(self.enabled_entity)
        #        assert temp, ('Entity not found: {} {} {}'.format(__name__, self.id, self.entity))
        
        self.hass.listen_state(self.enabled_state_callback, self.enabled_entity)
        self.enabled_state = enabled_state_transform( self.hass.get_state(self.enabled_entity) )
        #        assert self.enabled_state, ('Entity not found: {} {} {}'.format(__name__, self.id, self.entity))
      else:
        self.enabled_state = True
        
      self.update_status()
      #      self.hass.log('{}Condition inititilizing done'.format(self.prefix()), level='ERROR')
    except Exception as e:
      raise ValueError("Condition Error: name={} id={} e={}".format(__name__, self.id, e))
      

  def try_get_state(self, entity_id):
    try:
      state = self.hass.get_state(entity_id=entity_id)
      return state
    except:
      self.hass.log("{}: Failed to get_state for entity_id: {}".format(__name__, entity_id))
      return None

          
  # Callback if the entity containing the timeout_time changes
  def timeout_state_callback(self, entity, attribute, old, new, kwargs):
    try:
      self.timeout_time2 = float(new)
      if debug: self.hass.log('{}Timeout state changed to <{}>'.format(self.prefix(), self.timeout_time2), level='INFO')
    except Exception as e:
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))


  # Callback if the entity containing the enabled_time changes
  def enabled_state_callback(self, entity, attribute, old, new, kwargs):
    try:
      self.enabled_state = enabled_state_transform(new)
      if debug: self.hass.log('{}Enabled state changed to <{}>'.format(self.prefix(), self.enabled_state), level='ERROR')
    except Exception as e:
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))


  def update_time_status(self):
    try:
      #      self.hass.log('{}update_time_status'.format(self.prefix(), level='ERROR'))
      
      if self.years is None and self.months is None and self.weeks is None and self.days is None and self.weekdays is None and self.hours is None and self.minutes is None:
        self.time_status = True
      else:
        if self.time_handle == None:
          callback_time = datetime.now()
        
          callback_time = callback_time.replace(microsecond=0)
          callback_time = callback_time.replace(second=0) + timedelta(minutes=1)
          callback_interval = 60
          if self.minutes == None:
            callback_time = callback_time.replace(minute=0) + timedelta(hours=1)
            callback_interval = 3600
            if self.hours == None:
              callback_time = callback_time.replace(hour=0) + timedelta(days=1)
              callback_interval = 24*3600
            
          #          self.hass.log('{}callback: {} every {}'.format(self.prefix(), callback_time, callback_interval), level='INFO')
          self.time_handle = self.hass.run_every(self.time_callback, callback_time, callback_interval)
      
        now = datetime.now()
        self.time_status = ( (not self.years or now.year in self.years) and
                             (not self.months or now.month in self.months) and
                             (not self.days or now.day in self.days) and
                             (not self.hours or now.hour in self.hours) and
                             (not self.minutes or now.minute in self.minutes) and
                             (not self.weeks or now.isocalendar()[1] in self.weeks) and
                             (not self.weekdays or now.weekday() in self.weekdays) )

        #        self.hass.log('{}callback: time_status={} self.minutes={} now.minute={} now.weekday={}'.format(self.prefix(), self.time_status, self.minutes, now.minute, now.weekday()), level='ERROR')
    #      self.hass.log('{}update_time_status done'.format(self.prefix(), level='ERROR'))
        
    except Exception as e:
      raise ValueError("update_time_status Error: name={} id={} e={}".format(__name__, self.id, e))

      
  def time_callback(self, kwargs):
    try:
      #      self.hass.log('{}time_callback'.format(self.prefix(), level='INFO'))

      self.update_time_status()
      self.check()
    except Exception as e:
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))
      
   
  def condition_state_callback(self, entity, attribute, old, new, kwargs):
    try:
      if debug: self.hass.log('{}Condition state changed from <{}> to <{}>'.format(self.prefix(), old, new), level='ERROR')
      self.condition_state_change(new)
    except Exception as e:
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))
      

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
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))
    

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
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))
       
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
          #          self.hass.log('{}activate timer {}s'.format(self.prefix(), timeout_time), level='INFO')
          self.timer_handle = self.hass.run_in(self.timer_callback, timeout_time)
          self.timeout_status = False
        else:
          self.hass.log('{}activate timer - already active?!'.format(self.prefix()), level='ERROR')
        
      else:
        #      self.hass.log('{}Timeout is disabled'.format(self.prefix()), level='INFO')
        self.timeout_status = True
  
      self.check()
    except Exception as e:
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))
      
      
  # This is the callback function when timeout timer expires
  def timer_callback(self, kwargs):
    try:
      if debug: self.hass.log('{}Timer callback'.format(self.prefix()), level='INFO')
      self.timeout_status = True
      self.timer_handle = None
      self.check()
    except Exception as e:
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))
    

  # This is the callback function when stability timer expires
  def stability_callback(self, kwargs):
    try:
      if debug: self.hass.log('{}Stability callback'.format(self.prefix()), level='INFO')
      self.stability_status = True
      self.stability_handle = None
      self.check()
    except Exception as e:
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))


  # Will update status of this condition
  def update_status(self):
    #    self.hass.log('{}update_status'.format(self.prefix()), level='ERROR')
    try:
      self.status = self.enabled and self.enabled_state and self.timeout_status and self.entity_status and self.stability_status and self.time_status
      if debug: self.hass.log('{}update_status enabled/enabled_state/timeout/state/stability/time = {}/{}/{}/{}/{}/{} = {}'.format(self.prefix(), self.enabled, self.enabled_state, self.timeout_status, self.entity_status, self.stability_status, self.time_status, self.status), level='INFO')
    except Exception as e:
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))
    

  # Call check when something happened. If the status changes, all subscribing listeners will have their callback called  
  def check(self):
    if debug: self.hass.log('{}check'.format(self.prefix()), level='ERROR')
    try:
      self.update_status()
      
      if not self.last_status == self.status:
        if debug: self.hass.log('{}check change status from {} to {}'.format(self.prefix(), self.last_status, self.status), level='ERROR')

        if self.only_posedge:
          if (self.last_status == False) and (self.status == True):
            # Pos-edge

            #            self.hass.log('{}Posedge ok {} to {}'.format(self.prefix(), self.last_status, self.status), level='ERROR')
            # Announce True to listeners
            self.announce_to_callbacks(True)
            
            #            self.hass.log('{}Posedge - setting status back to false'.format(self.prefix()), level='ERROR')
            # Announce False to listeners
            self.announce_to_callbacks(False)

            # Set back status to the currently correct value. Not needed?
            self.status = True
          elif self.status == False:
            #            self.hass.log('{}Posedge reset {} to {}'.format(self.prefix(), self.last_status, self.status), level='ERROR')
            self.last_status = self.status
            
          #          else:
            #            self.hass.log('{}Posedge blocking {} to {}'.format(self.prefix(), self.last_status, self.status), level='ERROR')

        else:
            # Announce change to listeners
            self.announce_to_callbacks(self.status)
            self.last_status = self.status
            
    except Exception as e:
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))


  # Function to call all callbacks
  def announce_to_callbacks(self, value):
      old_status = self.status
      self.status = value
      for callback in self.callbacks:

        # --- This type of code results in infinit recursion ---
        #          for callback in self.callbacks:
        #             callback()
        if debug: self.hass.log('{}announce_to_callbacks'.format(self.prefix()), level='ERROR')
        try:
          self.hass.run_in(callback, 0)
        except Exception as e:
          raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))

      self.status = old_status
  
  # Function called from super object to register a callback function
  def add_callback(self, callback):
    try:
      self.callbacks.append(callback)
    except Exception as e:
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))
      

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
      raise ValueError("Error: name={} id={} e={}".format(__name__, self.id, e))
        
