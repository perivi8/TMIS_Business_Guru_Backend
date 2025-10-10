# Staff Assignment Locking - Complete Example

## Scenario: 2 Clients (1 Old, 1 New)

### Initial State
- **Client A**: Enquiry from 3 days ago, no staff assigned (OLD)
- **Client B**: Enquiry from today, no staff assigned (NEW)

### API Response Format

```json
{
  "enquiries": [
    {
      "_id": "client_b_id",
      "wati_name": "Client B",
      "date": "2025-10-10T10:00:00Z",
      "staff": "",
      "is_old_enquiry": false,
      "enquiry_age_days": 0,
      
      // Staff Dropdown Control Fields
      "staff_dropdown_enabled": false,
      "staff_dropdown_clickable": false,
      "staff_dropdown_reason": "New enquiry - assign staff to 1 old enquiry(ies) first",
      "staff_dropdown_ui_state": "disabled_locked",
      "can_assign_staff": false
    },
    {
      "_id": "client_a_id", 
      "wati_name": "Client A",
      "date": "2025-10-07T10:00:00Z",
      "staff": "",
      "is_old_enquiry": true,
      "enquiry_age_days": 3,
      
      // Staff Dropdown Control Fields
      "staff_dropdown_enabled": true,
      "staff_dropdown_clickable": true,
      "staff_dropdown_reason": "Old enquiry - staff assignment required to unlock others",
      "staff_dropdown_ui_state": "enabled_priority",
      "can_assign_staff": true
    }
  ],
  "staff_lock_status": {
    "locked": true,
    "reason": "Staff assignments locked: 1 old enquiries without staff assignment. Assign staff to an old enquiry first to unlock.",
    "unassigned_old_enquiries": 1,
    "assigned_enquiries": 0
  }
}
```

## Frontend Implementation Guide

### HTML/JavaScript Example

```html
<!-- Client B (New) - COMPLETELY DISABLED -->
<select 
  id="staff_select_client_b" 
  disabled
  style="opacity: 0.5; cursor: not-allowed;"
  title="New enquiry - assign staff to 1 old enquiry(ies) first">
  <option>Select Staff</option>
</select>

<!-- Client A (Old) - ENABLED WITH PRIORITY -->
<select 
  id="staff_select_client_a" 
  class="priority-highlight"
  style="border: 2px solid orange;"
  title="Old enquiry - staff assignment required to unlock others">
  <option value="">Select Staff</option>
  <option value="John">John</option>
  <option value="Mary">Mary</option>
</select>
```

### React/Vue Component Example

```javascript
// For each enquiry in the list
const StaffDropdown = ({ enquiry }) => {
  const dropdownProps = {
    disabled: !enquiry.staff_dropdown_clickable,
    className: `staff-dropdown ${enquiry.staff_dropdown_ui_state}`,
    title: enquiry.staff_dropdown_reason
  };

  // Prevent click events if not clickable
  const handleClick = (e) => {
    if (!enquiry.staff_dropdown_clickable) {
      e.preventDefault();
      e.stopPropagation();
      alert(enquiry.staff_dropdown_reason);
    }
  };

  return (
    <select 
      {...dropdownProps}
      onClick={handleClick}
      onChange={handleStaffChange}
    >
      <option value="">Select Staff</option>
      {staffOptions.map(staff => (
        <option key={staff.id} value={staff.name}>
          {staff.name}
        </option>
      ))}
    </select>
  );
};
```

### CSS Styling

```css
/* Normal enabled dropdown */
.staff-dropdown.enabled {
  border: 1px solid #ccc;
  cursor: pointer;
}

/* Priority enabled (old enquiry needing assignment) */
.staff-dropdown.enabled_priority {
  border: 2px solid #ff9800;
  background-color: #fff3e0;
  cursor: pointer;
}

/* Completely disabled (new enquiry when locked) */
.staff-dropdown.disabled_locked {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: #f5f5f5;
  pointer-events: none; /* Prevents any click events */
}

/* Error state */
.staff-dropdown.disabled_error {
  opacity: 0.5;
  cursor: not-allowed;
  border: 1px solid #f44336;
}
```

## Behavior Flow

### Step 1: Initial State (Locked)
- **Client A (Old)**: ✅ Dropdown ENABLED, clickable, highlighted
- **Client B (New)**: ❌ Dropdown DISABLED, not clickable, grayed out

### Step 2: Assign Staff to Client A
```javascript
// When user assigns staff to Client A
PUT /api/enquiries/client_a_id
{
  "staff": "John"
}

// Response: Success
```

### Step 3: After Assignment (Unlocked)
```json
{
  "enquiries": [
    {
      "_id": "client_b_id",
      "staff_dropdown_enabled": true,
      "staff_dropdown_clickable": true,
      "staff_dropdown_ui_state": "enabled",
      "can_assign_staff": true
    },
    {
      "_id": "client_a_id",
      "staff": "John",
      "staff_dropdown_enabled": true,
      "staff_dropdown_clickable": true,
      "staff_dropdown_ui_state": "enabled",
      "can_assign_staff": true
    }
  ],
  "staff_lock_status": {
    "locked": false,
    "reason": "Staff assignments unlocked: 1 enquiries have staff assigned."
  }
}
```

### Step 4: Final State (Unlocked)
- **Client A (Old)**: ✅ Dropdown ENABLED, can change staff
- **Client B (New)**: ✅ Dropdown ENABLED, can assign staff

## UI States Summary

| UI State | Enabled | Clickable | Visual Style | Use Case |
|----------|---------|-----------|--------------|----------|
| `enabled` | ✅ | ✅ | Normal | All unlocked |
| `enabled_priority` | ✅ | ✅ | Highlighted/Orange | Old enquiry needing assignment |
| `disabled_locked` | ❌ | ❌ | Grayed out | New enquiry when locked |
| `disabled_error` | ❌ | ❌ | Red border | Error state |

## Key Points for Frontend

1. **Use `staff_dropdown_clickable`** to control if dropdown responds to clicks
2. **Use `staff_dropdown_ui_state`** for CSS classes and styling
3. **Use `staff_dropdown_reason`** for tooltips and user messages
4. **Use `is_old_enquiry`** to understand enquiry age context
5. **Monitor `staff_lock_status.locked`** for global state changes

This implementation ensures that new enquiries are **completely disabled** until old enquiries get staff assigned, exactly as requested!
