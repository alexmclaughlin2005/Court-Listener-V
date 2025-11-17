# Opinion Text Download Options

## The Challenge

The `search_opinion` CSV file contains actual opinion text and is **30-50GB uncompressed**. CourtListener doesn't make this easily downloadable due to size.

---

## ✅ **Recommended Solution: Use CourtListener API**

Instead of downloading a massive CSV, fetch opinion text on-demand from CourtListener's API.

### Option A: Hybrid Approach (Best for Your Use Case)

**Strategy:** Keep your metadata, fetch text from CourtListener API when needed

**Advantages:**
- ✅ No huge download required
- ✅ Always up-to-date opinion text
- ✅ Fits within Railway storage limits
- ✅ Can implement later caching if needed

**Implementation:**
1. Keep current database (metadata only)
2. When user views a case, fetch opinion text from CourtListener API
3. Optionally cache in database for popular cases

### API Endpoint
```
https://www.courtlistener.com/api/rest/v3/opinions/{opinion_id}/
```

**Example:**
```bash
curl "https://www.courtlistener.com/api/rest/v3/opinions/403793/" \
  -H "Authorization: Token YOUR_API_TOKEN"
```

---

## Alternative Options

### Option B: Request Bulk Data from CourtListener

**Steps:**
1. Create account: https://www.courtlistener.com/register/
2. Email: info@free.law
3. Request access to bulk opinion data
4. They may provide a custom download link

**Timeline:** 1-3 days response time

---

### Option C: Download Selective Opinions via API

**Strategy:** Fetch only opinions for cases you've imported

**Python Script:**
```python
import requests
import psycopg2
import time

API_TOKEN = "your_token_here"
headers = {"Authorization": f"Token {API_TOKEN}"}

# Connect to your database
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Get opinion IDs from your database
cursor.execute("SELECT id FROM search_opinion WHERE plain_text IS NULL LIMIT 1000")
opinion_ids = [row[0] for row in cursor.fetchall()]

# Fetch opinion text from API
for opinion_id in opinion_ids:
    url = f"https://www.courtlistener.com/api/rest/v3/opinions/{opinion_id}/"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        plain_text = data.get('plain_text')
        html = data.get('html')

        # Update database
        cursor.execute("""
            UPDATE search_opinion
            SET plain_text = %s, html = %s
            WHERE id = %s
        """, (plain_text, html, opinion_id))
        conn.commit()
        print(f"✓ Updated opinion {opinion_id}")

    # Rate limit: 5 requests/second
    time.sleep(0.2)
```

**Pros:** Get exactly what you need
**Cons:** Rate limited, takes time for many opinions

---

### Option D: Link to CourtListener (Quick Fix)

**Strategy:** Don't store opinion text, just link to it

**Modify Frontend:**
```typescript
// In CaseDetailPage.tsx
{opinions.length === 0 || !opinions[0].plain_text ? (
  <a
    href={`https://www.courtlistener.com/opinion/${opinions[0]?.id}/`}
    className="text-blue-600 hover:underline"
    target="_blank"
  >
    View Full Opinion on CourtListener →
  </a>
) : (
  <div>{opinions[0].plain_text}</div>
)}
```

**Pros:** Immediate solution, no storage needed
**Cons:** External dependency, users leave your site

---

## 🎯 My Recommendation

**Use Option A: Hybrid Approach**

1. **Short-term:** Add "View on CourtListener" links (Option D)
2. **Long-term:** Implement API fetching (Option A or C)
3. **Optional:** Cache popular opinions in your database

### Why This Works:
- ✅ No 50GB download required
- ✅ Stays within Railway limits
- ✅ Users get opinion text when needed
- ✅ Can optimize later with caching

---

## Implementation Steps

### Step 1: Get CourtListener API Token

1. Visit: https://www.courtlistener.com/register/
2. Create account
3. Go to: https://www.courtlistener.com/api/rest-info/
4. Generate API token

### Step 2: Add API Integration

**Backend Route:**
```python
# backend/app/api/v1/opinions.py
@router.get("/opinions/{opinion_id}/fetch-text")
async def fetch_opinion_text(opinion_id: int):
    """Fetch opinion text from CourtListener API"""
    api_token = settings.COURTLISTENER_API_TOKEN
    url = f"https://www.courtlistener.com/api/rest/v3/opinions/{opinion_id}/"

    response = requests.get(url, headers={"Authorization": f"Token {api_token}"})
    if response.status_code == 200:
        data = response.json()
        return {
            "plain_text": data.get('plain_text'),
            "html": data.get('html'),
            "source": "courtlistener_api"
        }
    raise HTTPException(status_code=404, detail="Opinion not found")
```

### Step 3: Update Frontend

```typescript
// Fetch text on demand
const fetchOpinionText = async (opinionId: number) => {
  const response = await fetch(
    `${API_URL}/api/v1/opinions/${opinionId}/fetch-text`
  );
  return response.json();
};
```

---

## Storage Comparison

| Approach | Storage | Download | Updates |
|----------|---------|----------|---------|
| Full CSV Import | 30-50 GB | Days | Manual |
| API Hybrid | ~100 MB | Minutes | Auto |
| Cache Popular | ~1-2 GB | Hours | Auto |
| Link Only | 0 GB | None | Auto |

---

## Next Steps

1. **Decide on approach** (I recommend Hybrid/API)
2. **Get API token** from CourtListener
3. **Implement API fetching** OR add external links
4. **Test with a few cases**
5. **Deploy to production**

This avoids the massive download while still providing full opinion text to users!
