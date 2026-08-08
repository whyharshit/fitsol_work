"""
ESG Dashboard Backend API Server
Serves ESG data from JSON files to the React frontend
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import json
import glob
from pathlib import Path
import csv
import io

app = FastAPI(
    title="ESG Analytics API",
    description="API for serving ESG data from BRSR reports",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to ESG JSON outputs
ESG_DATA_PATH = Path(__file__).parent / "esg_outputs"

# Cache for loaded data
companies_cache: Dict[str, Any] = {}
all_companies: List[Dict[str, Any]] = []


def load_all_companies():
    """Load all company ESG data from JSON files"""
    global all_companies, companies_cache
    
    if all_companies:
        return all_companies
    
    json_files = glob.glob(str(ESG_DATA_PATH / "*.json"))
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            company_id = data.get('metadata', {}).get('company_id', '')
            company_name = data.get('metadata', {}).get('company_name', '')
            
            # Calculate scores from data points
            data_points = data.get('data_points', [])
            env_score = calculate_pillar_score(data_points, 'E')
            social_score = calculate_pillar_score(data_points, 'S')
            gov_score = calculate_pillar_score(data_points, 'G')
            
            # Extract key metrics
            company_data = {
                'id': company_id,
                'name': company_name,
                'year': data.get('metadata', {}).get('year', ''),
                'source_url': data.get('metadata', {}).get('source_url', ''),
                'envScore': env_score,
                'socialScore': social_score,
                'govScore': gov_score,
                'scope1': get_data_point_value(data_points, 'Scope 1 emissions (absolute)', 0),
                'scope2': get_data_point_value(data_points, 'Scope 2 emissions (LB & MB)', 0),
                'totalEnergy': get_data_point_value(data_points, 'Total Energy Consumed (A+B+C+D+E+F)', 0),
                'waterUsage': get_data_point_value(data_points, 'Net Water Consumption', 0),
                'wasteGenerated': get_data_point_value(data_points, 'Total Waste Generated (A+B+C+D+E+F+G+H)', 0),
                'workforce': get_data_point_value(data_points, 'Total Workforce', 0),
                'genderDiversity': get_data_point_value(data_points, 'Gender Diversity (Total Emp)', 0),
                'attrition': get_data_point_value(data_points, 'Attrition (Employees)', 0),
                'data_points': data_points,
                'metadata': data.get('metadata', {})
            }
            
            all_companies.append(company_data)
            companies_cache[company_id] = company_data
            
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue
    
    return all_companies


def calculate_pillar_score(data_points: List[Dict], pillar: str) -> int:
    """Calculate a score for a pillar based on data points"""
    pillar_points = [dp for dp in data_points if dp.get('esg_pillar') == pillar]
    
    if not pillar_points:
        return 50  # Default score
    
    # Calculate score based on disclosure completeness
    disclosed = sum(1 for dp in pillar_points if dp.get('value') not in [None, 'NA', 'Not Disclosed', 'null'])
    total = len(pillar_points)
    
    if total == 0:
        return 50
    
    # Base score from disclosure rate
    disclosure_rate = (disclosed / total) * 100
    
    # Adjust based on key metrics
    score = int(disclosure_rate * 0.7 + 30)  # Weighted score
    
    return min(100, max(0, score))


def get_data_point_value(data_points: List[Dict], name: str, default: Any = None):
    """Get value for a specific data point"""
    for dp in data_points:
        if dp.get('data_point') == name:
            value = dp.get('value')
            if value is None or value == 'NA' or value == 'Not Disclosed' or value == 'null':
                return default
            return value
    return default


@app.on_event("startup")
async def startup_event():
    """Load data on startup"""
    load_all_companies()
    print(f"Loaded {len(all_companies)} companies")


@app.get("/")
async def root():
    return {"message": "ESG Analytics API", "version": "1.0.0"}


@app.get("/api/companies")
async def get_companies(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    filter: str = Query("all")
):
    """Get paginated list of companies"""
    companies = load_all_companies()
    
    # Filter by search term
    if search:
        companies = [c for c in companies if search.lower() in c['name'].lower() or search.lower() in c['id'].lower()]
    
    # Filter by score
    if filter == "high":
        companies = [c for c in companies if (c['envScore'] + c['socialScore'] + c['govScore']) / 3 >= 80]
    elif filter == "medium":
        companies = [c for c in companies if 60 <= (c['envScore'] + c['socialScore'] + c['govScore']) / 3 < 80]
    elif filter == "low":
        companies = [c for c in companies if (c['envScore'] + c['socialScore'] + c['govScore']) / 3 < 60]
    
    # Pagination
    total = len(companies)
    start = (page - 1) * limit
    end = start + limit
    
    return {
        "companies": companies[start:end],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@app.get("/api/companies/{company_id}")
async def get_company(company_id: str):
    """Get single company by ID"""
    load_all_companies()
    
    if company_id not in companies_cache:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return companies_cache[company_id]


@app.get("/api/companies/{company_id}/esg")
async def get_company_esg(company_id: str):
    """Get detailed ESG data for a company"""
    load_all_companies()
    
    if company_id not in companies_cache:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company = companies_cache[company_id]
    return {
        "company_id": company_id,
        "company_name": company['name'],
        "data_points": company.get('data_points', []),
        "metadata": company.get('metadata', {})
    }


@app.get("/api/statistics")
async def get_statistics():
    """Get aggregated statistics"""
    companies = load_all_companies()
    
    if not companies:
        return {"error": "No data available"}
    
    total = len(companies)
    avg_env = sum(c['envScore'] for c in companies) / total
    avg_social = sum(c['socialScore'] for c in companies) / total
    avg_gov = sum(c['govScore'] for c in companies) / total
    
    # Emissions stats
    total_scope1 = sum(c.get('scope1', 0) or 0 for c in companies)
    total_scope2 = sum(c.get('scope2', 0) or 0 for c in companies)
    
    return {
        "totalCompanies": total,
        "avgEnvScore": round(avg_env, 1),
        "avgSocialScore": round(avg_social, 1),
        "avgGovScore": round(avg_gov, 1),
        "avgOverallScore": round((avg_env + avg_social + avg_gov) / 3, 1),
        "totalScope1": total_scope1,
        "totalScope2": total_scope2,
        "avgEmissions": round((total_scope1 + total_scope2) / total, 1) if total > 0 else 0
    }


@app.get("/api/emissions")
async def get_emissions_data(limit: int = Query(10, ge=1, le=50)):
    """Get emissions data for charts"""
    companies = load_all_companies()
    
    # Sort by total emissions and get top N
    sorted_companies = sorted(
        companies,
        key=lambda c: (c.get('scope1', 0) or 0) + (c.get('scope2', 0) or 0),
        reverse=True
    )[:limit]
    
    return {
        "data": [
            {
                "name": c['name'][:15],
                "scope1": c.get('scope1', 0) or 0,
                "scope2": c.get('scope2', 0) or 0
            }
            for c in sorted_companies
        ]
    }


@app.get("/api/search")
async def search_companies(q: str = Query(..., min_length=1)):
    """Search companies by name or ID"""
    companies = load_all_companies()
    
    results = [
        {"id": c['id'], "name": c['name'], "year": c['year']}
        for c in companies
        if q.lower() in c['name'].lower() or q.lower() in c['id'].lower()
    ][:20]  # Limit to 20 results
    
    return {"results": results}


@app.get("/api/export")
async def export_data(format: str = Query("csv")):
    """Export all data as CSV"""
    companies = load_all_companies()
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Company ID', 'Company Name', 'Year', 'Environmental Score',
            'Social Score', 'Governance Score', 'Scope 1 Emissions',
            'Scope 2 Emissions', 'Total Energy', 'Water Usage',
            'Waste Generated', 'Workforce', 'Gender Diversity', 'Attrition'
        ])
        
        # Data rows
        for c in companies:
            writer.writerow([
                c['id'], c['name'], c['year'], c['envScore'],
                c['socialScore'], c['govScore'], c.get('scope1', ''),
                c.get('scope2', ''), c.get('totalEnergy', ''),
                c.get('waterUsage', ''), c.get('wasteGenerated', ''),
                c.get('workforce', ''), c.get('genderDiversity', ''),
                c.get('attrition', '')
            ])
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=esg_data.csv"}
        )
    
    elif format == "json":
        return {"companies": companies}
    
    raise HTTPException(status_code=400, detail="Invalid format. Use 'csv' or 'json'")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
