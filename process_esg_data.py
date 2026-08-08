"""
Process ESG JSON files - Extract ALL data points for comprehensive dashboard
"""
import os
import json
import glob
from pathlib import Path

ESG_DATA_PATH = Path("esg_outputs")
OUTPUT_PATH = Path("esg-dashboard/public/data")

def get_value(data_points, name, default=None):
    """Get value for a specific data point"""
    for dp in data_points:
        if dp.get('data_point') == name:
            value = dp.get('value')
            if value is None or value == 'NA' or value == 'Not Disclosed' or value == 'null' or value == '':
                return default
            return value
    return default

def get_numeric(data_points, name, default=0):
    """Get numeric value"""
    val = get_value(data_points, name, default)
    if val is None or val == default:
        return default
    try:
        return float(val)
    except:
        return default

def calculate_pillar_score(data_points, pillar):
    """Calculate disclosure-based score"""
    pillar_points = [dp for dp in data_points if dp.get('esg_pillar') == pillar]
    if not pillar_points:
        return 50
    disclosed = sum(1 for dp in pillar_points if dp.get('value') not in [None, 'NA', 'Not Disclosed', 'null', ''])
    total = len(pillar_points)
    if total == 0:
        return 50
    return min(100, max(0, int((disclosed / total) * 70 + 30)))

def process_company(file_path):
    """Process a single company JSON file with ALL data points"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        metadata = data.get('metadata', {})
        dp = data.get('data_points', [])
        
        company_id = metadata.get('company_id', Path(file_path).stem)
        company_name = metadata.get('company_name', company_id.replace('_', ' ').title())
        
        # Calculate totals
        scope1 = get_numeric(dp, 'Scope 1 emissions (absolute)', 0)
        scope2 = get_numeric(dp, 'Scope 2 emissions (LB & MB)', 0)
        scope3 = get_numeric(dp, 'Scope 3 emissions (total)', 0)
        total_emissions = scope1 + scope2 + scope3
        
        return {
            'id': company_id,
            'name': company_name,
            'year': metadata.get('year', '2024-25'),
            'source_url': metadata.get('source_url', ''),
            'source_type': metadata.get('source_type', 'BRSR'),
            
            # Scores
            'envScore': calculate_pillar_score(dp, 'E'),
            'socialScore': calculate_pillar_score(dp, 'S'),
            'govScore': calculate_pillar_score(dp, 'G'),
            
            # EMISSIONS
            'scope1': scope1,
            'scope2': scope2,
            'scope3': scope3,
            'totalEmissions': total_emissions,
            'emissionsIntensityRevenue': get_numeric(dp, 'Emissions Intensity (Revenue)', 0),
            'emissionsIntensityPhysical': get_value(dp, 'Emissions Intensity (Physical)'),
            'emissionsReductionTarget': get_value(dp, 'Emissions Reduction Target'),
            'emissionsBaselineYear': get_value(dp, 'Emissions Baseline Year'),
            
            # Scope 3 Categories
            'scope3Cat1': get_numeric(dp, 'Scope 3 Cat 1: Purchased Goods', 0),
            'scope3Cat3': get_numeric(dp, 'Scope 3 Cat 3: Fuel/Energy Related', 0),
            'scope3Cat5': get_numeric(dp, 'Scope 3 Cat 5: Waste Generated', 0),
            'scope3Cat6': get_numeric(dp, 'Scope 3 Cat 6: Business Travel', 0),
            'scope3Cat7': get_numeric(dp, 'Scope 3 Cat 7: Employee Commuting', 0),
            'scope3Cat8': get_numeric(dp, 'Scope 3 Cat 8: Upstream Leased Assets', 0),
            'scope3Cat11': get_numeric(dp, 'Scope 3 Cat 11: Use of Sold Products', 0),
            'scope3Cat14': get_numeric(dp, 'Scope 3 Cat 14: Franchises', 0),
            
            # Air Emissions
            'nox': get_value(dp, 'NOx (Nitrogen Oxides)'),
            'sox': get_value(dp, 'SOx (Sulfur Oxides)'),
            'pm10': get_value(dp, 'Particulate Matter (PM-10)'),
            'pm25': get_value(dp, 'Particulate Matter (PM-2.5)'),
            
            # Climate Strategy
            'climateRiskAssessment': get_value(dp, 'Climate Risk Assessment'),
            'transitionPlan': get_value(dp, 'Transition Plan'),
            'netZeroCommitment': get_value(dp, 'Net Zero Commitment'),
            'netZeroTargetYear': get_value(dp, 'Net Zero Target Year'),
            'sbtiStatus': get_value(dp, 'SBTi Status'),
            'tcfdAlignment': get_value(dp, 'TCFD Alignment'),
            
            # ENERGY
            'totalEnergy': get_numeric(dp, 'Total Energy Consumed (A+B+C+D+E+F)', 0),
            'renewableElectricity': get_numeric(dp, 'Renewable Electricity Consumption (A)', 0),
            'renewableFuel': get_numeric(dp, 'Renewable Fuel Consumption (B)', 0),
            'renewableOther': get_numeric(dp, 'Renewable Energy from Other Sources (C)', 0),
            'totalRenewable': get_numeric(dp, 'Total Renewable Energy (A+B+C)', 0),
            'nonRenewableElectricity': get_numeric(dp, 'Non-Renewable Electricity Consumption (D)', 0),
            'nonRenewableFuel': get_numeric(dp, 'Non-Renewable Fuel Consumption (E)', 0),
            'nonRenewableOther': get_numeric(dp, 'Non-Renewable Energy from Other Sources (F)', 0),
            'totalNonRenewable': get_numeric(dp, 'Total Non-Renewable Energy (D+E+F)', 0),
            'renewablePercent': get_numeric(dp, 'Renewable Electricity %', 0),
            'energyIntensityRevenue': get_numeric(dp, 'Energy Intensity per Rupee of Turnover', 0),
            'energyIntensityPhysical': get_value(dp, 'Energy Intensity (Physical Output)'),
            'onsiteRenewable': get_value(dp, 'Onsite Renewable Capacity'),
            'independentEnergyAssessment': get_value(dp, 'Independent Energy Assessment'),
            'iso50001': get_value(dp, 'ISO 50001 Certified'),
            
            # WASTE
            'totalWaste': get_numeric(dp, 'Total Waste Generated (A+B+C+D+E+F+G+H)', 0),
            'plasticWaste': get_numeric(dp, 'Plastic Waste (A)', 0),
            'eWaste': get_numeric(dp, 'E-Waste (B)', 0),
            'bioMedicalWaste': get_numeric(dp, 'Bio-Medical Waste (C)', 0),
            'constructionWaste': get_numeric(dp, 'Construction & Demolition Waste (D)', 0),
            'batteryWaste': get_numeric(dp, 'Battery Waste (E)', 0),
            'radioactiveWaste': get_numeric(dp, 'Radioactive Waste (F)', 0),
            'otherHazardousWaste': get_numeric(dp, 'Other Hazardous Waste (G)', 0),
            'otherNonHazardousWaste': get_numeric(dp, 'Other Non-Hazardous Waste (H)', 0),
            'hazardousWaste': get_numeric(dp, 'Hazardous Waste', 0),
            'wasteRecycledPercent': get_numeric(dp, 'Waste Recycled %', 0),
            'incinerationVolume': get_numeric(dp, 'Incineration Volume', 0),
            'landfillVolume': get_numeric(dp, 'Landfill Volume', 0),
            'wasteIntensity': get_numeric(dp, 'Waste Intensity per Rupee of Turnover', 0),
            'recycledMaterialContent': get_numeric(dp, 'Recycled Material Content', 0),
            'plasticUsage': get_value(dp, 'Plastic Usage'),
            
            # WATER
            'totalWaterWithdrawal': get_numeric(dp, 'Total Water Withdrawal', 0),
            'netWaterConsumption': get_numeric(dp, 'Net Water Consumption', 0),
            'waterRecycledPercent': get_numeric(dp, 'Water Recycled %', 0),
            'effluentDischarge': get_numeric(dp, 'Effluent Discharge Volume', 0),
            'waterStressedLocations': get_value(dp, 'Water Stressed Locations'),
            'zldStatus': get_value(dp, 'ZLD Status'),
            
            # ENVIRONMENTAL GOVERNANCE
            'envPolicy': get_value(dp, 'Env Policy Published'),
            'iso14001': get_value(dp, 'ISO 14001 Certified'),
            'greenCapex': get_numeric(dp, 'Green CapEx %', 0),
            'greenRnD': get_numeric(dp, 'Green R&D %', 0),
            'envFines': get_numeric(dp, 'Env Fines/Penalties', 0),
            'supplierEnvReqs': get_value(dp, 'Supplier Env Requirements'),
            'cpcbCompliance': get_value(dp, 'CPCB/SPCB Compliance'),
            'productCarbonFootprint': get_value(dp, 'Product Carbon Footprint'),
            
            # SOCIAL - WORKFORCE
            'totalWorkforce': get_numeric(dp, 'Total Workforce', 0),
            'trainingHours': get_value(dp, 'Training Hours'),
            'csrSpend': get_numeric(dp, 'CSR Spend', 0),
            'supplierSocialAudits': get_value(dp, 'Supplier Social Audits'),
            
            # SOCIAL - DIVERSITY
            'genderDiversityBoard': get_numeric(dp, 'Gender Diversity (Board)', 0),
            'genderDiversityPermEmp': get_numeric(dp, 'Gender Diversity (Perm Emp)', 0),
            'genderDiversityTotal': get_numeric(dp, 'Gender Diversity (Total Emp)', 0),
            
            # SOCIAL - ATTRITION & SAFETY
            'attritionEmployees': get_numeric(dp, 'Attrition (Employees)', 0),
            'attritionWorkers': get_value(dp, 'Attrition (Workers)'),
            'ltifrEmployees': get_numeric(dp, 'LTIFR (Employees)', 0),
            'ltifrWorkers': get_numeric(dp, 'LTIFR (Workers)', 0),
            'iso45001': get_value(dp, 'ISO 45001 Certified'),
            'humanRightsPolicy': get_value(dp, 'Human Rights Policy'),
            
            # GOVERNANCE
            'antiCorruptionPolicy': get_value(dp, 'Anti-Corruption Policy'),
            'whistleblowerMechanism': get_value(dp, 'Whistleblower Mechanism'),
            'esgOversightCommittee': get_value(dp, 'ESG Oversight Committee'),
            'boardIndependence': get_value(dp, 'Board Independence %'),
            'esgLinkedPay': get_value(dp, 'ESG Linked Pay'),
            'legalCases': get_value(dp, 'Legal Cases'),
            
            # EXTERNAL RATINGS
            'cdpScore': get_value(dp, 'CDP Score'),
            'djsiInclusion': get_value(dp, 'DJSI Inclusion'),
            'ecoVadisMedal': get_value(dp, 'EcoVadis Medal'),
            'msciRating': get_value(dp, 'MSCI Rating'),
            'sustainalyticsScore': get_value(dp, 'Sustainalytics Score'),
            'ungcParticipant': get_value(dp, 'UNGC Participant'),
            'patScheme': get_value(dp, 'PAT Scheme'),
            'pliAutoParticipation': get_value(dp, 'PLI Auto Participation'),
            
            # Raw data points for detail view
            'data_points': dp
        }
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def main():
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    json_files = list(ESG_DATA_PATH.glob("*.json"))
    print(f"Found {len(json_files)} JSON files")
    
    companies = []
    companies_detail = {}
    
    for i, file_path in enumerate(json_files):
        if (i + 1) % 100 == 0:
            print(f"Processing {i + 1}/{len(json_files)}...")
        
        company = process_company(file_path)
        if company:
            companies_detail[company['id']] = company
            # Summary without raw data_points
            summary = {k: v for k, v in company.items() if k != 'data_points'}
            companies.append(summary)
    
    print(f"Successfully processed {len(companies)} companies")
    
    # Calculate aggregated statistics
    if companies:
        total = len(companies)
        stats = {
            'totalCompanies': total,
            'avgEnvScore': round(sum(c['envScore'] for c in companies) / total, 1),
            'avgSocialScore': round(sum(c['socialScore'] for c in companies) / total, 1),
            'avgGovScore': round(sum(c['govScore'] for c in companies) / total, 1),
            'totalScope1': sum(c.get('scope1', 0) or 0 for c in companies),
            'totalScope2': sum(c.get('scope2', 0) or 0 for c in companies),
            'totalScope3': sum(c.get('scope3', 0) or 0 for c in companies),
            'avgEmissions': round(sum(c.get('totalEmissions', 0) or 0 for c in companies) / total, 1),
            'totalEnergy': sum(c.get('totalEnergy', 0) or 0 for c in companies),
            'totalWater': sum(c.get('netWaterConsumption', 0) or 0 for c in companies),
            'totalWaste': sum(c.get('totalWaste', 0) or 0 for c in companies),
            'avgGenderDiversity': round(sum(c.get('genderDiversityTotal', 0) or 0 for c in companies) / total, 1),
            'avgAttrition': round(sum(c.get('attritionEmployees', 0) or 0 for c in companies) / total, 1),
        }
    else:
        stats = {}
    
    # Save files
    with open(OUTPUT_PATH / 'companies.json', 'w', encoding='utf-8') as f:
        json.dump({'companies': companies, 'stats': stats}, f)
    print(f"Saved companies.json")
    
    with open(OUTPUT_PATH / 'companies_detail.json', 'w', encoding='utf-8') as f:
        json.dump(companies_detail, f)
    print(f"Saved companies_detail.json")
    
    # Emissions chart data
    emissions_data = sorted(
        [{'name': c['name'][:18], 'scope1': c.get('scope1', 0) or 0, 'scope2': c.get('scope2', 0) or 0, 'scope3': c.get('scope3', 0) or 0} 
         for c in companies if (c.get('scope1', 0) or 0) + (c.get('scope2', 0) or 0) > 0],
        key=lambda x: x['scope1'] + x['scope2'] + x['scope3'],
        reverse=True
    )[:15]
    
    with open(OUTPUT_PATH / 'emissions.json', 'w', encoding='utf-8') as f:
        json.dump({'data': emissions_data}, f)
    
    print("\n✅ Data processing complete!")

if __name__ == "__main__":
    main()
