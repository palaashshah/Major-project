const API_BASE = "http://localhost:8000"

export async function createInvestor(data: {
    name: string        // required — must be provided
    total_aum?: number  // "?" optional — can be skipped
    investment_horizon?: string
    risk_score?: string
    assigned_manager_id: string
    demographics?: object
    preferences_constraints?: object
}) {
    const response = await fetch(`${API_BASE}/investors/`, // this is a template literal. Instead of "http://localhost:8000" + "/investors/"
                                                           //  fetch sends the HTTP request. await means "wait for the response before continuing".
        {
            method: 'POST', // tells fetch which HTTP method to use, default is "GET"
            headers: {
                "Content-Type": "application/json" // tells the API you're sending JSON
            },
            body: JSON.stringify(data) // converts your JavaScript object into a JSON string. The API can't receive a JavaScript object directly
        }   
    );     
    return response.json(); //  converts the response text back into a JavaScript object so you can use it in your code.
}

export async function getInvestors() {
    const response = await fetch(`${API_BASE}/investors/`)
    return response.json();
}
export async function getInvestor(investorId: string) {
    const response = await fetch(`${API_BASE}/investors/${investorId}`)
    return response.json();
}

export async function getInteractions(investorId: string) {
    try {
        const response = await fetch(`${API_BASE}/interactions/?investor_id=${investorId}`)
                                                            // ↑
                                                            // /interactions/?investor_id=abc123  ← investor_id is a QUESTION to the path
                                                            // /interactions/abc123       ← investor_id IS the path
                                                            // If you use a Path Parameter (/interactions/123), you are saying that "Interaction 123" is a unique destination, like a specific house.
                                                            // If you use a Query Parameter (/interactions?investor_id=123), you are saying "Show me the general interactions list, but filter it so I only see things belonging to this investor."                          
        const data = await response.json()
        // backend might return an array directly, or wrapped — handle both
        return Array.isArray(data) ? data : []
    } catch {
        return []  // if fetch fails entirely, return empty array instead of crashing
    }
}

export async function createInteraction(data: {
    investor_id: string
    interaction_type: string
    notes: string
    manager_id: string
    timestamp?: string
}){
     const response = await fetch(`${API_BASE}/interactions/`,
        {
            method: 'POST', 
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        }   
    );
    return response.json();
}

export async function updateInvestor(investorId: string, data: {
  name?: string
  total_aum?: number
  investment_horizon?: string
  risk_score?: string
  demographics?: object
  preferences_constraints?: object
}) {
  const response = await fetch(`${API_BASE}/investors/${investorId}`, // ← ID in the URL
    {
      method: 'PUT', // ← PUT means "replace this specific resource with new data"
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data) // only send the fields you want to change
    }
  )
  return response.json()
}

export async function getAllInteractions(){
    const response = await fetch(`${API_BASE}/interactions/`)
    return response.json();
}