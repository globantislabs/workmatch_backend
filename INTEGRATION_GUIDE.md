# Quick Integration Guide

## Step-by-Step Instructions

### 1. Add Edit Modals to Admin HTML

Open `public/admin-responsive.html` and add these two modals before the closing `</body>` tag (after line 635, after the Blog Modal):

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
```

### 2. Update Table Headers

Find line ~360 (Careers table header) and replace with:
```html
<thead><tr><th>#</th><th>Name</th><th>Position</th><th>Email</th><th>Phone</th><th>Resume</th><th>Date</th><th>Actions</th></tr></thead>
```

Find line ~365 (Hire Talent table header) and replace with:
```html
<thead><tr><th>#</th><th>Name</th><th>Company</th><th>Email</th><th>Phone</th><th>Inquiry</th><th>Date</th><th>Actions</th></tr></thead>
```

### 3. Update renderCareers Function

Find the `renderCareers` function (around line 430) and replace it with:

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
```

### 4. Update renderHire Function

Find the `renderHire` function (around line 445) and replace it with:

```javascript
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

### 5. Add JavaScript Functions

Add these functions before the `logout()` function at the end of the script section (around line 630):

```javascript
// ── Application Edit ──────────────────────────────────────────────────────────
let editAppId=null;
function openAppModal(a){editAppId=a?.id||null;document.getElementById('aName').value=a?.full_name||'';document.getElementById('aEmail').value=a?.email||'';document.getElementById('aPhone').value=a?.phone||'';document.getElementById('aPosition').value=a?.position||'';document.getElementById('appModal').classList.add('on');}
function closeAppModal(){document.getElementById('appModal').classList.remove('on');}
function editApplication(id){openAppModal(allCareers.find(a=>a.id===id));}
async function saveApplication(){const btn=document.getElementById('btnSaveApp'),n=document.getElementById('aName').value.trim(),e=document.getElementById('aEmail').value.trim(),p=document.getElementById('aPhone').value.trim(),pos=document.getElementById('aPosition').value.trim();if(!n||!e||!p||!pos){toast('Fill all fields','err');return;}btn.classList.add('busy');btn.textContent='Saving…';const fd=new FormData();fd.append('full_name',n);fd.append('email',e);fd.append('phone',p);fd.append('position',pos);try{const r=await api(`/admin/api/applications/${editAppId}`,{method:'PUT',body:fd});if(!r.ok)throw new Error();const i=allCareers.findIndex(a=>a.id===editAppId);if(i>-1)allCareers[i]={...allCareers[i],full_name:n,email:e,phone:p,position:pos};renderCareers(allCareers);closeAppModal();toast('Updated','ok');}catch(e){toast('Failed','err');}finally{btn.classList.remove('busy');btn.textContent='Save';}}
async function deleteApplication(id){if(!confirm('Delete?'))return;const row=document.getElementById('ar-'+id);if(row)row.classList.add('removing');try{const r=await api(`/admin/api/applications/${id}`,{method:'DELETE'});if(!r.ok)throw new Error();setTimeout(()=>{allCareers=allCareers.filter(a=>a.id!==id);renderCareers(allCareers);toast('Deleted','ok');},250);}catch{if(row)row.classList.remove('removing');toast('Failed','err');}}

// ── Hire Talent Edit ──────────────────────────────────────────────────────────
let editHireId=null;
function openHireModal(h){editHireId=h?.id||null;document.getElementById('hName').value=h?.full_name||'';document.getElementById('hCompany').value=h?.company_name||'';document.getElementById('hEmail').value=h?.email||'';document.getElementById('hPhone').value=h?.phone||'';document.getElementById('hInquiry').value=h?.inquiry||'';document.getElementById('hireModal').classList.add('on');}
function closeHireModal(){document.getElementById('hireModal').classList.remove('on');}
function editHireRequest(id){openHireModal(allHire.find(h=>h.id===id));}
async function saveHireRequest(){const btn=document.getElementById('btnSaveHire'),n=document.getElementById('hName').value.trim(),c=document.getElementById('hCompany').value.trim(),e=document.getElementById('hEmail').value.trim(),p=document.getElementById('hPhone').value.trim(),inq=document.getElementById('hInquiry').value.trim();if(!n||!c||!e||!p||!inq){toast('Fill all fields','err');return;}btn.classList.add('busy');btn.textContent='Saving…';const fd=new FormData();fd.append('full_name',n);fd.append('company_name',c);fd.append('email',e);fd.append('phone',p);fd.append('inquiry',inq);try{const r=await api(`/admin/api/hire-talent/${editHireId}`,{method:'PUT',body:fd});if(!r.ok)throw new Error();const i=allHire.findIndex(h=>h.id===editHireId);if(i>-1)allHire[i]={...allHire[i],full_name:n,company_name:c,email:e,phone:p,inquiry:inq};renderHire(allHire);closeHireModal();toast('Updated','ok');}catch(e){toast('Failed','err');}finally{btn.classList.remove('busy');btn.textContent='Save';}}
async function deleteHireRequest(id){if(!confirm('Delete?'))return;const row=document.getElementById('hr-'+id);if(row)row.classList.add('removing');try{const r=await api(`/admin/api/hire-talent/${id}`,{method:'DELETE'});if(!r.ok)throw new Error();setTimeout(()=>{allHire=allHire.filter(h=>h.id!==id);renderHire(allHire);toast('Deleted','ok');},250);}catch{if(row)row.classList.remove('removing');toast('Failed','err');}}
```

## That's It!

After making these changes:
1. Restart your FastAPI server
2. Navigate to `/admin/login`
3. You'll see "Forgot password?" link
4. In the admin dashboard, you'll see Edit buttons for Applications and Hire Talent records
5. Test the full CRUD functionality

All backend endpoints are already in place and working!
