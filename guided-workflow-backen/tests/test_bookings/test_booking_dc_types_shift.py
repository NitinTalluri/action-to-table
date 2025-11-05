from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
from api.v2.services.manager_bookings import ServiceTypeFlag

def get_shifted(current_service_type, proposed_service_type):
    shifted_service_from = (
        None
        if current_service_type in proposed_service_type
        else current_service_type & ~proposed_service_type
    )
    return shifted_service_from

class Booking(RuleBasedStateMachine):
    service_type = ServiceTypeFlag.HW_SW
    prev_service_type = ServiceTypeFlag.HW_SW
    
    @rule()
    def set_service_type_hw_sw(self):
        prev_st = self.service_type
        self.service_type = ServiceTypeFlag.HW_SW
        self.prev_service_type = prev_st
        
    @rule()
    def set_service_type_sw(self):
        prev_st = self.service_type
        self.service_type = ServiceTypeFlag.SW
        self.prev_service_type = prev_st
        
    @rule()
    def set_service_type_hw(self):
        prev_st = self.service_type
        self.service_type = ServiceTypeFlag.HW
        self.prev_service_type = prev_st
        
    @invariant()
    def check_shifted(self):
        shifted = get_shifted(self.prev_service_type, self.service_type)
        
        if self.prev_service_type == ServiceTypeFlag.HW_SW:
            if self.service_type == ServiceTypeFlag.HW:
                # We should detect that SW was shifted out
                assert shifted == ServiceTypeFlag.SW
            elif self.service_type == ServiceTypeFlag.SW:
                # We should detect that HW was shifted out
                assert shifted == ServiceTypeFlag.HW
            else:
                # No shift should be detected
                assert shifted is None
        
        elif self.prev_service_type == ServiceTypeFlag.HW:
            if self.service_type == ServiceTypeFlag.HW_SW:
                # No shift should be detected
                assert shifted is None
            elif self.service_type == ServiceTypeFlag.SW:
                # We should detect that HW was shifted out
                assert shifted == ServiceTypeFlag.HW
            else:
                # No shift should be detected
                assert shifted is None
                
        elif self.prev_service_type == ServiceTypeFlag.SW:
            if self.service_type == ServiceTypeFlag.HW_SW:
                # No shift should be detected
                assert shifted is None
            elif self.service_type == ServiceTypeFlag.HW:
                # We should detect that SW was shifted out
                assert shifted == ServiceTypeFlag.SW
            else:
                # No shift should be detected
                assert shifted is None
                
        

BookingsTest = Booking.TestCase            