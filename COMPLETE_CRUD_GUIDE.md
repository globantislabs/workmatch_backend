# Complete CRUD & Change Password Integration Guide

## Overview
This guide adds full CRUD functionality for Applications and Hire Talent, plus a Change Password feature for admins.

## Backend Changes (Already Applied)

### 1. CRUD Endpoints (Already in main.py)
- ✅ `GET /admin/api/applications/{id}` - Get single application
- ✅ `PUT /admin/api/applications/{id}` - Update application
- ✅ `DELETE /admin/api/applications/{id}` - Delete application
- ✅ `GET /admin/api/hire-talent/{id}` - Get single hire request
- ✅ `PUT /admin/api/hire-talent/{id}` - Update hire request
- ✅ `DELETE /admin/api/hire-talent/{id}` - Delete hire request

### 2. Change Password Endpoint (Just Added)
- ✅ `POST /admin/api/change-password` - Change admin password
  - Requires: oldPassword, password, passwordConfirm
  - Validates current password before changing
  - Minimum 8 characters

## Frontend Changes Required

### Step 1: Update Table Headers

Open `public/admin-responsive.html` and find the table headers:

**Line ~219 (Careers table):**
```html
<table><thead><tr><th>#</th><th>Name</th><th>Position</th><th>Email</th><th>Phone</th><th>Resume</th><th>Date</th><th>Actions</th></tr></thead>
```

**Line ~224 (Hire Talent table):**
```html
<table><thead><tr><th>#</th><th>Name</th><th>Company</th><th>Email</th><th>Phone</th><th>Inquiry</th><th>Date</th><th>Actions</th></tr></thead>
```

### Step 2: Update Sidebar (Add Change Password Button)

Find the sidebar footer section (around line 120) and replace:

```html
<div class="sb-foot">
  <button class="btn" style="width:100%;margin-bottom:.5rem" onclick="openPasswordModal()">Change Password</button>
  <button class="btn" style="width:100%" onclick="logout()">Logout</button>
</div>
```

### Step 3: Add Modals

Add these three modals before the closing `</body>` tag (after the Blog Modal, around line 635):

```html
<!-- Application Edit Modal -->
<div class="modal-bg" id="appModal">
  <div class="modal">
    <div class="mhdr"><span class="mtitle">Edit Application</span><button class="mclose" onclick="closeAppModal()">×</button></div>
    <div class="mbody">
      <div class="fr">
        <div class="fg2"><label class="flabel">Full Name *</label><input class="fc" id="aName"></div>
        <div class="fg2"><label class="flabel">Email *</label><input class="fc" id="aEmail" type="email"></div>
      </div>
      <div class="fr">
        <div class="fg2"><label class="flabel">Phone *</label><input class="fc" id="aPhone"></div>
        <div class="fg2"><label class="flabel">Position *</label><input class="fc" id="aPosition"></div>
      </div>
    </div>
    <div class="mfoot">
      <button class="btn" onclick="closeAppModal()">Cancel</button>
      <button class="btn btn-p" id="btnSaveApp" onclick="saveApplication()">Save</button>
    </div>
  </div>
</div>

<!-- Hire Talent Edit Modal -->
<div class="modal-bg" id="hireModal">
  <div class="modal">
    <div class="mhdr"><span class="mtitle">Edit Hire Request</span><button class="mclose" onclick="closeHireModal()">×</button></div>
    <div class="mbody">
      <div class="fr">
        <div class="fg2"><label class="flabel">Full Name *</label><input class="fc" id="hName"></div>
        <div class="fg2"><label class="flabel">Company *</label><input class="fc" id="hCompany"></div>
      </div>
      <div class="fr">
        <div class="fg2"><label class="flabel">Email *</label><input class="fc" id="hEmail" type="email"></div>
        <div class="fg2"><label class="flabel">Phone *</label><input class="fc" id="hPhone"></div>
      </div>
      <div class="fg2"><label class="flabel">Inquiry *</label><textarea class="fc" id="hInquiry" rows="4"></textarea></div>
    </div>
    <div class="mfoot">
      <button class="btn" onclick="closeHireModal()">Cancel</button>
      <button class="btn btn-p" id="btnSaveHire" onclick="saveHireRequest()">Save</button>
    </div>
  </div>
</div>

<!-- Change Password Modal -->
<div class="modal-bg" id="passwordModal">
  <div class="modal" style="max-width:480px">
    <div class="mhdr"><span class="mtitle">Change Password</span><button class="mclose" onclick="closePasswordModal()">×</button></div>
    <div class="mbody">
      <div class="fg2"><label class="flabel">Current Password *</label><input class="fc" id="pCurrent" type="password"></div>
      <div class="fg2"><label class="flabel">New Password *</label><input class="fc" id="pNew" type="password" minlength="8"></div>
      <div class="fg2"><label class="flabel">Confirm New Password *</label><input class="fc" id="pConfirm" type="password" minlength="8"></div>
      <div style="font-size:11px;color:var(--t3);margin-top:.5rem">Password must be at least 8 characters</div>
    </div>
    <div class="mfoot">
      <button class="btn" onclick="closePasswordModal()">Cancel</button>
      <button class="btn btn-p" id="btnSavePassword" onclick="savePassword()">Change Password</button>
    </div>
  </div>
</div>
```

### Step 4: Replace Render Functions

Find and replace the `renderCareers` and `renderHire` functions (around line 430):

```javascript
function renderCareers(data) {
  const tb = document.getElementById('tb-careers');
  if (!data.length) { tb.innerHTML='<tr><td colspan="8"><div class="empty">No applications found</div></td></tr>'; return; }
  tb.innerHTML = data.map((a,i)=>`<tr id="ar-${a.id}">
    <td>${i+1}</td><td>${esc(a.full_name)}</td>
    <td><span class="badge badge-b">${esc(a.position)}</span></td>
    <td><a href="mailto:${esc(a.email)}" style="color:var(--p)">${esc(a.email)}</a></td>
    <td>${esc(a.phone)}</td>
    <td>${a.cv_url?`<a href="${a.cv_url}" target="_blank" class="btn btn-sm">↓ CV</a>`:'—'}</td>
    <td>${fmtDate(a.created_at)}</td>
    <td style="white-space:nowrap">
      <button class="btn btn-sm" onclick="editApplication('${a.id}')">Edit</button>
      <button class="btn btn-sm btn-r" onclick="deleteApplication('${a.id}')">Del</button>
    </td>
  </tr>`).join('');
}

function renderHire(data) {
  const tb = document.getElementById('tb-hire');
  if (!data.length) { tb.innerHTML='<tr><td colspan="8"><div class="empty">No hire requests found</div></td></tr>'; return; }
  tb.innerHTML = data.map((h,i)=>`<tr id="hr-${h.id}">
    <td>${i+1}</td><td>${esc(h.full_name)}</td><td>${esc(h.company_name)}</td>
    <td><a href="mailto:${esc(h.email)}" style="color:var(--p)">${esc(h.email)}</a></td>
    <td>${esc(h.phone)}</td>
    <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(h.inquiry)}">${esc(h.inquiry)}</td>
    <td>${fmtDate(h.created_at)}</td>
    <td style="white-space:nowrap">
      <button class="btn btn-sm" onclick="editHireRequest('${h.id}')">Edit</button>
      <button class="btn btn-sm btn-r" onclick="deleteHireRequest('${h.id}')">Del</button>
    </td>
  </tr>`).join('');
}
```

### Step 5: Add JavaScript Functions

Add these functions before the `logout()` function (around line 630):

```javascript
// ── Application CRUD ──────────────────────────────────────────────────────────
let editAppId=null;
function openAppModal(a){editAppId=a?.id||null;document.getElementById('aName').value=a?.full_name||'';document.getElementById('aEmail').value=a?.email||'';document.getElementById('aPhone').value=a?.phone||'';document.getElementById('aPosition').value=a?.position||'';document.getElementById('appModal').classList.add('on');setTimeout(()=>document.getElementById('aName').focus(),50);}
function closeAppModal(){document.getElementById('appModal').classList.remove('on');}
function editApplication(id){openAppModal(allCareers.find(a=>a.id===id));}
async function saveApplication(){const btn=document.getElementById('btnSaveApp'),n=document.getElementById('aName').value.trim(),e=document.getElementById('aEmail').value.trim(),p=document.getElementById('aPhone').value.trim(),pos=document.getElementById('aPosition').value.trim();if(!n||!e||!p||!pos){toast('Fill all fields','err');return;}btn.classList.add('busy');btn.textContent='Saving…';const fd=new FormData();fd.append('full_name',n);fd.append('email',e);fd.append('phone',p);fd.append('position',pos);try{const r=await api(`/admin/api/applications/${editAppId}`,{method:'PUT',body:fd});if(!r.ok)throw new Error();const i=allCareers.findIndex(a=>a.id===editAppId);if(i>-1)allCareers[i]={...allCareers[i],full_name:n,email:e,phone:p,position:pos};renderCareers(allCareers);closeAppModal();toast('Updated','ok');}catch(e){toast('Failed','err');}finally{btn.classList.remove('busy');btn.textContent='Save';}}
async function deleteApplication(id){if(!confirm('Delete this application?'))return;const row=document.getElementById('ar-'+id);if(row)row.classList.add('removing');try{const r=await api(`/admin/api/applications/${id}`,{method:'DELETE'});if(!r.ok)throw new Error();setTimeout(()=>{allCareers=allCareers.filter(a=>a.id!==id);renderCareers(allCareers);toast('Deleted','ok');},250);}catch{if(row)row.classList.remove('removing');toast('Failed','err');}}

// ── Hire Talent CRUD ──────────────────────────────────────────────────────────
let editHireId=null;
function openHireModal(h){editHireId=h?.id||null;document.getElementById('hName').value=h?.full_name||'';document.getElementById('hCompany').value=h?.company_name||'';document.getElementById('hEmail').value=h?.email||'';document.getElementById('hPhone').value=h?.phone||'';document.getElementById('hInquiry').value=h?.inquiry||'';document.getElementById('hireModal').classList.add('on');setTimeout(()=>document.getElementById('hName').focus(),50);}
function closeHireModal(){document.getElementById('hireModal').classList.remove('on');}
function editHireRequest(id){openHireModal(allHire.find(h=>h.id===id));}
async function saveHireRequest(){const btn=document.getElementById('btnSaveHire'),n=document.getElementById('hName').value.trim(),c=document.getElementById('hCompany').value.trim(),e=document.getElementById('hEmail').value.trim(),p=document.getElementById('hPhone').value.trim(),inq=document.getElementById('hInquiry').value.trim();if(!n||!c||!e||!p||!inq){toast('Fill all fields','err');return;}btn.classList.add('busy');btn.textContent='Saving…';const fd=new FormData();fd.append('full_name',n);fd.append('company_name',c);fd.append('email',e);fd.append('phone',p);fd.append('inquiry',inq);try{const r=await api(`/admin/api/hire-talent/${editHireId}`,{method:'PUT',body:fd});if(!r.ok)throw new Error();const i=allHire.findIndex(h=>h.id===editHireId);if(i>-1)allHire[i]={...allHire[i],full_name:n,company_name:c,email:e,phone:p,inquiry:inq};renderHire(allHire);closeHireModal();toast('Updated','ok');}catch(e){toast('Failed','err');}finally{btn.classList.remove('busy');btn.textContent='Save';}}
async function deleteHireRequest(id){if(!confirm('Delete this hire request?'))return;const row=document.getElementById('hr-'+id);if(row)row.classList.add('removing');try{const r=await api(`/admin/api/hire-talent/${id}`,{method:'DELETE'});if(!r.ok)throw new Error();setTimeout(()=>{allHire=allHire.filter(h=>h.id!==id);renderHire(allHire);toast('Deleted','ok');},250);}catch{if(row)row.classList.remove('removing');toast('Failed','err');}}

// ── Change Password ───────────────────────────────────────────────────────────
function openPasswordModal(){document.getElementById('pCurrent').value='';document.getElementById('pNew').value='';document.getElementById('pConfirm').value='';document.getElementById('passwordModal').classList.add('on');setTimeout(()=>document.getElementById('pCurrent').focus(),50);}
function closePasswordModal(){document.getElementById('passwordModal').classList.remove('on');}
async function savePassword(){const btn=document.getElementById('btnSavePassword'),curr=document.getElementById('pCurrent').value,newP=document.getElementById('pNew').value,conf=document.getElementById('pConfirm').value;if(!curr||!newP||!conf){toast('Fill all fields','err');return;}if(newP.length<8){toast('Password must be at least 8 characters','err');return;}if(newP!==conf){toast('Passwords do not match','err');return;}btn.classList.add('busy');btn.textContent='Changing…';const fd=new FormData();fd.append('oldPassword',curr);fd.append('password',newP);fd.append('passwordConfirm',conf);try{const r=await api('/admin/api/change-password',{method:'POST',body:fd});if(!r.ok){const err=await r.json();throw new Error(err.detail||'Failed');}closePasswordModal();toast('Password changed successfully','ok');}catch(e){toast(e.message,'err');}finally{btn.classList.remove('busy');btn.textContent='Change Password';}}
```

## Testing Checklist

### Applications CRUD
- [ ] Click Edit button on an application
- [ ] Modify fields and save
- [ ] Verify changes appear in the table
- [ ] Click Delete button
- [ ] Confirm deletion works

### Hire Talent CRUD
- [ ] Click Edit button on a hire request
- [ ] Modify fields and save
- [ ] Verify changes appear in the table
- [ ] Click Delete button
- [ ] Confirm deletion works

### Change Password
- [ ] Click "Change Password" in sidebar
- [ ] Enter wrong current password - should show error
- [ ] Enter mismatched new passwords - should show error
- [ ] Enter password < 8 chars - should show error
- [ ] Enter correct current password and valid new password
- [ ] Verify password change succeeds
- [ ] Logout and login with new password

## API Endpoints Summary

### Applications
- `GET /admin/api/applications` - List all
- `GET /admin/api/applications/{id}` - Get one
- `PUT /admin/api/applications/{id}` - Update
- `DELETE /admin/api/applications/{id}` - Delete

### Hire Talent
- `GET /admin/api/hire-talent` - List all
- `GET /admin/api/hire-talent/{id}` - Get one
- `PUT /admin/api/hire-talent/{id}` - Update
- `DELETE /admin/api/hire-talent/{id}` - Delete

### Password Management
- `POST /api/auth/request-password-reset` - Request reset link
- `POST /api/auth/confirm-password-reset` - Confirm reset with token
- `POST /admin/api/change-password` - Change password (logged in)

## Deployment

After making the frontend changes, deploy with:

```bash
python3 deploy.py update
```

Or from local machine:

```bash
python3 deploy.py push
```

All backend endpoints are already in place and ready to use!
