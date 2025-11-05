import json
from pathlib import Path

import pytest
from sqlalchemy import text, select
from sqlmodel import Session

from api.v2.orm import V2User


@pytest.fixture
def data_dir() -> Path:
    """Create and return tests/data directory"""
    data_path = Path(__file__).parent.parent / "data"
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path


@pytest.fixture
def buying_program_ids(db_session: Session, data_dir: Path) -> dict[str, int]:
    """Query buying program IDs dynamically from database with file caching"""
    cache_file = data_dir / "buying_program_ids.json"
    
    # Try to load from cache
    if cache_file.exists():
        with cache_file.open('r', encoding='utf-8') as f:
            return json.load(f)
    
    # Query database if not cached
    query = text("""
        SELECT buying_program_type_id, buying_program_name
        FROM DC_BUYING_PROGRAMS 
        WHERE is_deleted = 'F'
        AND (buying_program_name ILIKE '%CXEA%SCALE%' 
             OR buying_program_name = 'CXEA - Designated')
    """)
    results = db_session.exec(query).all()
    
    program_map = {}
    for row in results:
        if 'CXEA' in row.buying_program_name.upper() and 'SCALE' in row.buying_program_name.upper():
            program_map['cxea_scale'] = row.buying_program_type_id
        elif row.buying_program_name == 'CXEA - Designated':
            program_map['cxea_designated'] = row.buying_program_type_id
    
    # Cache the results
    with cache_file.open('w', encoding='utf-8') as f:
        json.dump(program_map, f, indent=2)
    
    return program_map


@pytest.fixture 
def override_reason_id(db_session: Session, data_dir: Path) -> int:
    """Get a valid override reason ID for testing with file caching"""
    cache_file = data_dir / "override_reason_id.json"
    
    # Try to load from cache
    if cache_file.exists():
        with cache_file.open('r', encoding='utf-8') as f:
            data = json.load(f)
            return data['override_reason_id']
    
    # Query database if not cached
    query = text("""
        SELECT booking_override_reason_id 
        FROM DC_TYP_BOOKING_OVERRIDE 
        WHERE is_deleted = 'F'
        LIMIT 1
    """)
    result = db_session.exec(query).scalar_one()
    
    # Cache the results
    with cache_file.open('w', encoding='utf-8') as f:
        json.dump({'override_reason_id': result}, f, indent=2)
    
    return result


@pytest.fixture
def regular_booking_contract_id(db_session: Session, buying_program_ids: dict[str, int], data_dir: Path) -> int:
    """Find a regular (non-CXEA) unclaimed booking contract with file caching"""
    cache_file = data_dir / "regular_booking_contract_id.json"
    
    # Try to load from cache
    if cache_file.exists():
        with cache_file.open('r', encoding='utf-8') as f:
            data = json.load(f)
            return data['booking_contract_id']
    
    # Query database if not cached
    cxea_scale_id = buying_program_ids.get('cxea_scale')
    
    query = text("""
        SELECT bc.booking_contract
        FROM DC_BOOKINGS_CONTRACTS bc
        WHERE bc.is_deleted = 'F'
        AND bc.claimed_and_managed_by IS NULL
        AND bc.buying_program_type_id != :cxea_scale_id
        AND bc.booking_contract > 0
        AND (
            (current_date <= dateadd('day', :look_ahead_days, agreement_end_date) 
                AND bc.booking_contract >= :id_threshold)
             OR
            (bc.booking_contract < :id_threshold and current_date < agreement_end_date)
        )
        LIMIT 1
    """)
    result = db_session.exec(query.bindparams(
        cxea_scale_id=cxea_scale_id,
        look_ahead_days=180,
        id_threshold=20400000
    )).scalar_one()
    
    # Cache the results
    with cache_file.open('w', encoding='utf-8') as f:
        json.dump({'booking_contract_id': result}, f, indent=2)
    
    return result


@pytest.fixture
def cxea_booking_contract_id(db_session: Session, buying_program_ids: dict[str, int], data_dir: Path) -> int:
    """Find a CXEA-Scale unclaimed booking contract with file caching"""
    cache_file = data_dir / "cxea_booking_contract_id.json"
    
    # Try to load from cache
    if cache_file.exists():
        with cache_file.open('r', encoding='utf-8') as f:
            data = json.load(f)
            return data['booking_contract_id']
    
    # Query database if not cached
    cxea_scale_id = buying_program_ids.get('cxea_scale')
    
    query = text("""
        SELECT bc.booking_contract
        FROM DC_BOOKINGS_CONTRACTS bc
        WHERE bc.is_deleted = 'F'
        AND bc.claimed_and_managed_by IS NULL  
        AND bc.buying_program_type_id = :cxea_scale_id
        AND bc.booking_contract > 0
        AND (
            (current_date <= dateadd('day', :look_ahead_days, agreement_end_date) 
                AND bc.booking_contract >= :id_threshold)
             OR
            (bc.booking_contract < :id_threshold and current_date < agreement_end_date)
        )
        LIMIT 1
    """)
    result = db_session.exec(query.bindparams(
        cxea_scale_id=cxea_scale_id,
        look_ahead_days=180,
        id_threshold=20400000
    )).scalar_one()
    
    # Cache the results
    with cache_file.open('w', encoding='utf-8') as f:
        json.dump({'booking_contract_id': result}, f, indent=2)
    
    return result


@pytest.fixture
def claimed_cxea_booking_contract_id(db_session: Session, buying_program_ids: dict[str, int], data_dir: Path) -> int:
    """Find a CXEA-Scale booking contract that IS claimed with file caching"""
    cache_file = data_dir / "claimed_cxea_booking_contract_id.json"
    
    # Try to load from cache
    if cache_file.exists():
        with cache_file.open('r', encoding='utf-8') as f:
            data = json.load(f)
            return data['booking_contract_id']
    
    # Query database if not cached
    cxea_scale_id = buying_program_ids.get('cxea_scale')
    
    query = text("""
        SELECT bc.booking_contract
        FROM DC_BOOKINGS_CONTRACTS bc
        WHERE bc.is_deleted = 'F'
        AND bc.claimed_and_managed_by IS NOT NULL  
        AND bc.buying_program_type_id = :cxea_scale_id
        AND bc.booking_contract > 0
        AND (
            (current_date <= dateadd('day', :look_ahead_days, agreement_end_date) 
                AND bc.booking_contract >= :id_threshold)
             OR
            (bc.booking_contract < :id_threshold and current_date < agreement_end_date)
        )
        LIMIT 1
    """)
    result = db_session.exec(query.bindparams(
        cxea_scale_id=cxea_scale_id,
        look_ahead_days=180,
        id_threshold=20400000
    )).scalar_one()
    
    # Cache the results
    with cache_file.open('w', encoding='utf-8') as f:
        json.dump({'booking_contract_id': result}, f, indent=2)
    
    return result


@pytest.fixture
def test_user_id() -> int:
    return 423

@pytest.fixture
def test_requestor(db_session, test_user_id):
    stmt = select(V2User).where(V2User.user_id == test_user_id)
    user = db_session.exec(stmt).scalar_one()
    
    # Return a V2User-like object (works across session boundaries)
    
    class MockUser:
        def __init__(self, user_id: int, cisco_cco_id: str):
            self.user_id = user_id
            self.cisco_cco_id = cisco_cco_id
            
    
    return MockUser(user.user_id, user.cisco_cco_id)


@pytest.fixture
def booking_original_state(db_session: Session):
    """Fixture to store and restore original booking state"""
    stored_states = {}
    
    def store_state(booking_contract: int):
        """Store original state of a booking contract"""
        query = text("""
            SELECT claimed_and_managed_by, buying_program_type_id
            FROM DC_BOOKINGS_CONTRACTS
            WHERE booking_contract = :booking_contract
        """)
        result = db_session.exec(query.bindparams(booking_contract=booking_contract)).first()
        stored_states[booking_contract] = {
            'claimed_and_managed_by': result.claimed_and_managed_by,
            'buying_program_type_id': result.buying_program_type_id
        }
    
    def restore_state(booking_contract: int):
        """Restore original state of a booking contract"""
        if booking_contract not in stored_states:
            return
            
        original = stored_states[booking_contract]
        
        # Restore booking contract state
        restore_query = text("""
            UPDATE DC_BOOKINGS_CONTRACTS 
            SET claimed_and_managed_by = :claimed_by,
                buying_program_type_id = :program_id
            WHERE booking_contract = :booking_contract
        """)
        db_session.exec(restore_query.bindparams(
            booking_contract=booking_contract,
            claimed_by=original['claimed_and_managed_by'],
            program_id=original['buying_program_type_id']
        ))
        
        # Remove any override entries created during test
        cleanup_override_query = text("""
            DELETE FROM DC_BOOKING_OVERRIDE 
            WHERE booking_contract = :booking_contract
        """)
        db_session.exec(cleanup_override_query.bindparams(booking_contract=booking_contract))
        
        db_session.commit()
    
    yield store_state, restore_state
    
    # Cleanup all stored states
    for booking_contract in stored_states:
        restore_state(booking_contract)


class TestCXEABookingOverrides:
    """Test CXEA override functionality for claiming process"""
    
    def test_claim_regular_booking_without_override(
        self, 
        db_session: Session, 
        regular_booking_contract_id: int, 
        buying_program_ids: dict[str, int],
        booking_original_state: tuple,
        test_requestor,
    ):
        """Test claiming a regular (non-CXEA) booking should work without override reason"""
        store_state, restore_state = booking_original_state
        booking_contract = regular_booking_contract_id
        
        # Store original state for cleanup
        store_state(booking_contract)
        
        try:
            # Verify booking is unclaimed initially
            check_claim_query = text("""
                SELECT claimed_and_managed_by, buying_program_type_id
                FROM DC_BOOKINGS_CONTRACTS
                WHERE booking_contract = :booking_contract
            """)
            original_state = db_session.exec(check_claim_query.bindparams(
                booking_contract=booking_contract
            )).first()
            
            assert original_state.claimed_and_managed_by is None, "Booking should be unclaimed initially"
            
            # Claim the booking without override reason
            from api.v2.services.manager_bookings import ManagerBookingsService
            from api.dependencies.queries import fetch_booking_service_types
            
            booking_types = fetch_booking_service_types(session=db_session)
            
            
            
            
            
            with ManagerBookingsService(db_session, booking_types, ignore_dispatch=True) as service:
                service.claim_booking(
                    requestor=test_requestor,
                    booking_contract=booking_contract,
                    renewal_sources=None,
                    dc_engagement_id_default=None,
                    booking_override_reason_id=None  # No override reason needed for regular bookings
                )
                db_session.commit()
            
            # Verify booking was claimed
            after_claim_state = db_session.exec(check_claim_query.bindparams(
                booking_contract=booking_contract
            )).first()
            
            assert after_claim_state.claimed_and_managed_by == test_requestor.user_id, "Booking should be claimed by user"
            
            # Verify NO override entry was created
            check_override_query = text("""
                SELECT booking_contract 
                FROM DC_BOOKING_OVERRIDE 
                WHERE booking_contract = :booking_contract AND is_deleted = 'F'
            """)
            override_entry = db_session.exec(check_override_query.bindparams(
                booking_contract=booking_contract
            )).first()
            
            assert override_entry is None, "No override entry should be created for regular bookings"
            
            print(f"PASS: Regular booking {booking_contract} claimed successfully without override")
            
        finally:
            restore_state(booking_contract)
    
    def test_claim_cxea_booking_with_override(
        self,
        db_session: Session,
        cxea_booking_contract_id: int,
        override_reason_id: int,
        buying_program_ids: dict[str, int],
        booking_original_state: tuple,
        test_requestor,
    ):
        """Test claiming a CXEA booking requires override reason and creates override entry"""
        store_state, restore_state = booking_original_state
        booking_contract = cxea_booking_contract_id
        
        # Store original state for cleanup
        store_state(booking_contract)
        
        try:
            # Verify booking is CXEA and unclaimed initially
            check_claim_query = text("""
                SELECT claimed_and_managed_by, buying_program_type_id
                FROM DC_BOOKINGS_CONTRACTS
                WHERE booking_contract = :booking_contract
            """)
            original_state = db_session.exec(check_claim_query.bindparams(
                booking_contract=booking_contract
            )).first()
            
            assert original_state.claimed_and_managed_by is None, "CXEA booking should be unclaimed initially"
            assert original_state.buying_program_type_id == buying_program_ids['cxea_scale'], "Should be CXEA-Scale booking"
            
            # Claim the CXEA booking WITH override reason
            from api.v2.services.manager_bookings import ManagerBookingsService
            from api.dependencies.queries import fetch_booking_service_types
            
            booking_types = fetch_booking_service_types(session=db_session)
            
            with ManagerBookingsService(db_session, booking_types, ignore_dispatch=True) as service:
                service.claim_booking(
                    requestor=test_requestor,
                    booking_contract=booking_contract,
                    renewal_sources=None,
                    dc_engagement_id_default=None,
                    booking_override_reason_id=override_reason_id  # Override reason required for CXEA
                )
                db_session.commit()
            
            # Verify booking was claimed and buying program updated
            after_claim_state = db_session.exec(check_claim_query.bindparams(
                booking_contract=booking_contract
            )).first()
            
            assert after_claim_state.claimed_and_managed_by == test_requestor.user_id, "CXEA booking should be claimed by user"
            assert after_claim_state.buying_program_type_id == buying_program_ids['cxea_designated'], \
                "Buying program should be updated to CXEA - Designated"
            
            # Verify override entry was created
            check_override_query = text("""
                SELECT booking_contract, booking_override_reason_id, created_by
                FROM DC_BOOKING_OVERRIDE 
                WHERE booking_contract = :booking_contract AND is_deleted = 'F'
            """)
            override_entry = db_session.exec(check_override_query.bindparams(
                booking_contract=booking_contract
            )).first()
            
            assert override_entry is not None, "Override entry should be created for CXEA bookings"
            assert override_entry.booking_override_reason_id == override_reason_id, \
                "Override entry should have correct reason ID"
            assert override_entry.created_by == test_requestor.cisco_cco_id, \
                "Override entry should be created by the claiming user"
            
            print(f"PASS: CXEA booking {booking_contract} claimed with override, buying program updated to CXEA - Designated")
            
        finally:
            restore_state(booking_contract)

    def test_reclaim_already_claimed_cxea_booking(
        self,
        db_session: Session,
        claimed_cxea_booking_contract_id: int,
        override_reason_id: int,
        buying_program_ids: dict[str, int],
        booking_original_state: tuple,
        test_requestor,
    ):
        """Test that CXEA booking can be reclaimed even if already claimed by another user"""
        store_state, restore_state = booking_original_state
        booking_contract = claimed_cxea_booking_contract_id
        
        # Store original state for cleanup
        store_state(booking_contract)
        
        try:
            # Verify booking is CXEA and already claimed initially
            check_claim_query = text("""
                SELECT claimed_and_managed_by, buying_program_type_id
                FROM DC_BOOKINGS_CONTRACTS
                WHERE booking_contract = :booking_contract
            """)
            original_state = db_session.exec(check_claim_query.bindparams(
                booking_contract=booking_contract
            )).first()
            
            assert original_state.claimed_and_managed_by is not None, "CXEA booking should be claimed initially"
            assert original_state.buying_program_type_id == buying_program_ids['cxea_scale'], "Should be CXEA-Scale booking"
            
            original_claimer = original_state.claimed_and_managed_by
            
            # Attempt to reclaim the CXEA booking WITH override reason
            from api.v2.services.manager_bookings import ManagerBookingsService
            from api.dependencies.queries import fetch_booking_service_types
            
            booking_types = fetch_booking_service_types(session=db_session)
            
            with ManagerBookingsService(db_session, booking_types, ignore_dispatch=True) as service:
                service.claim_booking(
                    requestor=test_requestor,
                    booking_contract=booking_contract,
                    renewal_sources=None,
                    dc_engagement_id_default=None,
                    booking_override_reason_id=override_reason_id  # Override reason required for CXEA
                )
                db_session.commit()
            
            # Verify booking was reclaimed and buying program updated
            after_claim_state = db_session.exec(check_claim_query.bindparams(
                booking_contract=booking_contract
            )).first()
            
            assert after_claim_state.claimed_and_managed_by == test_requestor.user_id, \
                f"CXEA booking should be reclaimed by user {test_requestor.user_id}, not {original_claimer}"
            assert after_claim_state.buying_program_type_id == buying_program_ids['cxea_designated'], \
                "Buying program should be updated to CXEA - Designated"
            
            # Verify override entry was created
            check_override_query = text("""
                SELECT booking_contract, booking_override_reason_id, created_by
                FROM DC_BOOKING_OVERRIDE 
                WHERE booking_contract = :booking_contract AND is_deleted = 'F'
            """)
            override_entry = db_session.exec(check_override_query.bindparams(
                booking_contract=booking_contract
            )).first()
            
            assert override_entry is not None, "Override entry should be created for CXEA reclaim"
            assert override_entry.booking_override_reason_id == override_reason_id, \
                "Override entry should have correct reason ID"
            assert override_entry.created_by == test_requestor.cisco_cco_id, \
                "Override entry should be created by the reclaiming user"
            
            print(f"PASS: Already claimed CXEA booking {booking_contract} successfully reclaimed from user {original_claimer} to user {test_requestor.user_id}")
            
        finally:
            restore_state(booking_contract)