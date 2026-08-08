import { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts'
import {
  Search, Leaf, Users, Shield, TrendingUp, Building2, Award, Target,
  ChevronLeft, ChevronRight, X, FileText, BarChart3, PieChart as PieChartIcon,
  Home, Settings, Database, Zap, Droplets, Trash2, ExternalLink, Download,
  AlertTriangle, Check, Wind, Factory, Recycle, Heart, Briefcase, Scale
} from 'lucide-react'
import './App.css'

const COLORS = {
  env: '#10b981', social: '#3b82f6', gov: '#8b5cf6', external: '#f59e0b',
  scope1: '#10b981', scope2: '#3b82f6', scope3: '#f59e0b',
  success: '#10b981', warning: '#f59e0b', danger: '#ef4444', info: '#06b6d4',
  purple: '#8b5cf6', pink: '#ec4899', orange: '#f97316', teal: '#14b8a6'
}

function App() {
  const [companies, setCompanies] = useState([])
  const [companiesDetail, setCompaniesDetail] = useState({})
  const [selectedCompany, setSelectedCompany] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [activeFilter, setActiveFilter] = useState('all')
  const [currentPage, setCurrentPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('environmental')
  const [emissionsData, setEmissionsData] = useState([])
  const [stats, setStats] = useState({})
  const [error, setError] = useState(null)
  const [viewMode, setViewMode] = useState('table')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const searchRef = useRef(null)
  const itemsPerPage = 12

  useEffect(() => {
    const loadData = async () => {
      try {
        const companiesRes = await fetch('/data/companies.json')
        if (!companiesRes.ok) throw new Error('Failed to load data. Run: python process_esg_data.py')
        const companiesData = await companiesRes.json()
        setCompanies(companiesData.companies || [])
        setStats(companiesData.stats || {})
        const detailRes = await fetch('/data/companies_detail.json')
        if (detailRes.ok) setCompaniesDetail(await detailRes.json())
        const emissionsRes = await fetch('/data/emissions.json')
        if (emissionsRes.ok) setEmissionsData((await emissionsRes.json()).data || [])
        setLoading(false)
      } catch (err) {
        setError(err.message)
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const filteredCompanies = useMemo(() => {
    return companies.filter(c => {
      const matchesSearch = c.name?.toLowerCase().includes(searchTerm.toLowerCase()) || c.id?.toLowerCase().includes(searchTerm.toLowerCase())
      if (activeFilter === 'all') return matchesSearch
      const avg = ((c.envScore || 0) + (c.socialScore || 0) + (c.govScore || 0)) / 3
      if (activeFilter === 'high') return matchesSearch && avg >= 80
      if (activeFilter === 'medium') return matchesSearch && avg >= 60 && avg < 80
      if (activeFilter === 'low') return matchesSearch && avg < 60
      return matchesSearch
    })
  }, [companies, searchTerm, activeFilter])

  const searchSuggestions = useMemo(() => {
    if (!searchTerm || searchTerm.length < 1) return []
    const term = searchTerm.toLowerCase()
    return companies
      .filter(c => c.name?.toLowerCase().includes(term) || c.id?.toLowerCase().includes(term))
      .slice(0, 8)
  }, [companies, searchTerm])

  // Close suggestions on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSearchSelect = useCallback((c) => {
    setShowSuggestions(false)
    setSearchTerm('')
    handleCompanySelect(c)
  }, [companiesDetail])

  const totalPages = Math.ceil(filteredCompanies.length / itemsPerPage)
  const paginatedCompanies = filteredCompanies.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)
  useEffect(() => { setCurrentPage(1) }, [searchTerm, activeFilter])

  const getScoreClass = (score) => score >= 80 ? 'excellent' : score >= 60 ? 'good' : score >= 40 ? 'average' : 'poor'
  const getOverallScore = (c) => Math.round(((c.envScore || 0) + (c.socialScore || 0) + (c.govScore || 0)) / 3)
  const formatNum = (n, dec = 0) => n === null || n === undefined || n === 0 ? 'N/A' : typeof n === 'number' ? n.toLocaleString(undefined, { maximumFractionDigits: dec }) : n
  const formatLarge = (n) => { if (n === null || n === undefined || n === '' || n === 0) return 'N/A'; if (typeof n === 'number') return n.toLocaleString(undefined, { maximumFractionDigits: 2 }); return n }

  const handleCompanySelect = (c) => {
    setSelectedCompany(companiesDetail[c.id] || c)
    setActiveTab('environmental')
  }

  if (error) return <div className="app"><div className="loading"><h2>Error</h2><p>{error}</p></div></div>

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <div className="logo-icon"><Leaf size={24} color="white" /></div>
            <div className="logo-text"><h1>Fitsol</h1><span>ESG Analytics Dashboard</span></div>
          </div>
        </div>
        <nav className="sidebar-nav">
          <div className="nav-section">
            <div className="nav-section-title">Overview</div>
            <div className="nav-item active"><Home size={20} /><span>Dashboard</span></div>
            <div className="nav-item"><Building2 size={20} /><span>Companies ({stats.totalCompanies?.toLocaleString() || 0})</span></div>
            <div className="nav-item"><BarChart3 size={20} /><span>Analytics</span></div>
          </div>
          <div className="nav-section">
            <div className="nav-section-title">ESG Pillars</div>
            <div className="nav-item"><Leaf size={20} /><span>Environmental</span></div>
            <div className="nav-item"><Users size={20} /><span>Social</span></div>
            <div className="nav-item"><Shield size={20} /><span>Governance</span></div>
          </div>
          <div className="nav-section">
            <div className="nav-section-title">Tools</div>
            <div className="nav-item"><Database size={20} /><span>BRSR Reports</span></div>
            <div className="nav-item"><Download size={20} /><span>Export</span></div>
          </div>
        </nav>
      </aside>

      <main className="main-content">
        <header className="header">
          <div className="header-left">
            <h2>ESG Analytics Dashboard</h2>
            <p>Monitor ESG performance across <strong>{stats.totalCompanies?.toLocaleString() || 0}</strong> Indian companies</p>
          </div>
          <div className="header-right">
            <div className="search-container" ref={searchRef}>
              <Search className="search-icon" size={20} />
              <input
                type="text"
                className="search-input"
                placeholder="Search companies..."
                value={searchTerm}
                onChange={(e) => { setSearchTerm(e.target.value); setShowSuggestions(true) }}
                onFocus={() => { if (searchTerm) setShowSuggestions(true) }}
                onKeyDown={(e) => { if (e.key === 'Escape') setShowSuggestions(false) }}
              />
              {showSuggestions && searchSuggestions.length > 0 && (
                <div className="search-dropdown">
                  {searchSuggestions.map(c => (
                    <div key={c.id} className="search-suggestion" onClick={() => handleSearchSelect(c)}>
                      <div className="suggestion-info">
                        <div className="suggestion-name">{c.name}</div>
                        <div className="suggestion-id">{c.id} • {c.year}</div>
                      </div>
                      <div className={`suggestion-score ${getScoreClass(getOverallScore(c))}`}>{getOverallScore(c)}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </header>

        {loading ? <div className="loading"><div className="spinner"></div><p>Loading ESG data...</p></div> : (
          <>
            {/* Summary Stats */}
            <div className="stats-grid">
              <StatCard color="env" icon={<Leaf size={24} />} value={`${stats.avgEnvScore || 0}%`} label="Avg Environmental" />
              <StatCard color="social" icon={<Users size={24} />} value={`${stats.avgSocialScore || 0}%`} label="Avg Social" />
              <StatCard color="gov" icon={<Shield size={24} />} value={`${stats.avgGovScore || 0}%`} label="Avg Governance" />
              <StatCard color="external" icon={<Building2 size={24} />} value={stats.totalCompanies?.toLocaleString() || 0} label="Total Companies" />
            </div>

            {/* Aggregated Metrics */}
            <div className="charts-grid">
              <div className="card"><div className="card-header"><h3 className="card-title">📊 Aggregate ESG Scores</h3></div>
                <div className="card-body"><div className="chart-container"><ResponsiveContainer>
                  <PieChart><Pie data={[{ name: 'Env', value: stats.avgEnvScore || 0, color: COLORS.env }, { name: 'Social', value: stats.avgSocialScore || 0, color: COLORS.social }, { name: 'Gov', value: stats.avgGovScore || 0, color: COLORS.gov }]} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={5} dataKey="value">{[COLORS.env, COLORS.social, COLORS.gov].map((c, i) => <Cell key={i} fill={c} />)}</Pie><Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', color: '#1e293b' }} /><Legend /></PieChart>
                </ResponsiveContainer></div></div>
              </div>
              <div className="card"><div className="card-header"><h3 className="card-title">🏭 Top Emitters (Scope 1, 2, 3)</h3></div>
                <div className="card-body"><div className="chart-container"><ResponsiveContainer>
                  <BarChart data={emissionsData} layout="vertical" margin={{ left: 80 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
                    <XAxis type="number" stroke="#64748b" />
                    <YAxis dataKey="name" type="category" stroke="#64748b" width={80} tick={{ fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', color: '#1e293b' }} />
                    <Legend /><Bar dataKey="scope1" stackId="a" fill={COLORS.scope1} name="Scope 1" /><Bar dataKey="scope2" stackId="a" fill={COLORS.scope2} name="Scope 2" /><Bar dataKey="scope3" stackId="a" fill={COLORS.scope3} name="Scope 3" />
                  </BarChart>
                </ResponsiveContainer></div></div>
              </div>
            </div>

            {/* Company Table */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Company ESG Overview ({filteredCompanies.length} results)</h3>
                <div className="filters">
                  <button className={`filter-btn ${activeFilter === 'all' ? 'active' : ''}`} onClick={() => setActiveFilter('all')}>All</button>
                  <button className={`filter-btn filter-high ${activeFilter === 'high' ? 'active' : ''}`} onClick={() => setActiveFilter('high')}>High ≥80</button>
                  <button className={`filter-btn filter-medium ${activeFilter === 'medium' ? 'active' : ''}`} onClick={() => setActiveFilter('medium')}>Medium 60-79</button>
                  <button className={`filter-btn filter-low ${activeFilter === 'low' ? 'active' : ''}`} onClick={() => setActiveFilter('low')}>Low &lt;60</button>
                </div>
              </div>
              <div className="company-table-container">
                <table className="company-table">
                  <thead><tr><th>Company</th><th>Year</th><th>ESG</th><th>Env</th><th>Social</th><th>Gov</th><th>Emissions</th><th>Energy</th><th>Actions</th></tr></thead>
                  <tbody>{paginatedCompanies.map(c => <tr key={c.id} onClick={() => handleCompanySelect(c)}><td><div className="company-name">{c.name}</div><div className="company-id">{c.id}</div></td><td>{c.year}</td><td><div className={`esg-score ${getScoreClass(getOverallScore(c))}`}>{getOverallScore(c)}</div></td><td><span className="pillar-pill E">{c.envScore}%</span></td><td><span className="pillar-pill S">{c.socialScore}%</span></td><td><span className="pillar-pill G">{c.govScore}%</span></td><td>{formatLarge(c.totalEmissions || c.scope1 + c.scope2)} {(c.totalEmissions || c.scope1 + c.scope2) ? <span className="unit-label">tCO2e</span> : ''}</td><td>{formatLarge(c.totalEnergy)} {c.totalEnergy ? <span className="unit-label">GJ</span> : ''}</td><td><button className="view-btn" onClick={e => { e.stopPropagation(); handleCompanySelect(c) }}>View</button></td></tr>)}</tbody>
                </table>
              </div>
              <div className="pagination">
                <button className="page-btn" onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1}><ChevronLeft size={18} /></button>
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => { let p = currentPage <= 3 ? i + 1 : currentPage >= totalPages - 2 ? totalPages - 4 + i : currentPage - 2 + i; if (p < 1 || p > totalPages) return null; return <button key={p} className={`page-btn ${currentPage === p ? 'active' : ''}`} onClick={() => setCurrentPage(p)}>{p}</button> })}
                <span className="page-info">Page {currentPage}/{totalPages}</span>
                <button className="page-btn" onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages}><ChevronRight size={18} /></button>
              </div>
            </div>
          </>
        )}
      </main>

      {selectedCompany && <CompanyModal company={selectedCompany} activeTab={activeTab} setActiveTab={setActiveTab} onClose={() => setSelectedCompany(null)} formatNum={formatNum} formatLarge={formatLarge} />}
    </div>
  )
}

function StatCard({ color, icon, value, label, subtitle }) {
  return <div className={`stat-card ${color}`}><div className="stat-icon">{icon}</div><div className="stat-value">{value}</div><div className="stat-label">{label}</div>{subtitle && <div className="stat-subtitle">{subtitle}</div>}</div>
}

function CompanyModal({ company: c, activeTab, setActiveTab, onClose, formatNum, formatLarge }) {
  const scope1 = c.scope1 || 0, scope2 = c.scope2 || 0, scope3 = c.scope3 || 0
  const totalEmissions = scope1 + scope2 + scope3
  const scopeData = [{ name: 'Scope 1', value: scope1, percent: totalEmissions ? ((scope1 / totalEmissions) * 100).toFixed(1) : 0 }, { name: 'Scope 2', value: scope2, percent: totalEmissions ? ((scope2 / totalEmissions) * 100).toFixed(1) : 0 }, { name: 'Scope 3', value: scope3, percent: totalEmissions ? ((scope3 / totalEmissions) * 100).toFixed(1) : 0 }]

  const scope3Categories = [
    { name: 'Purchased Goods', value: c.scope3Cat1 || 0 }, { name: 'Fuel/Energy', value: c.scope3Cat3 || 0 }, { name: 'Waste Generated', value: c.scope3Cat5 || 0 },
    { name: 'Business Travel', value: c.scope3Cat6 || 0 }, { name: 'Employee Commute', value: c.scope3Cat7 || 0 }, { name: 'Upstream Leased', value: c.scope3Cat8 || 0 },
    { name: 'Use of Products', value: c.scope3Cat11 || 0 }, { name: 'Franchises', value: c.scope3Cat14 || 0 }
  ].filter(x => x.value > 0)

  const wasteByCategory = [
    { name: 'Plastic', value: c.plasticWaste || 0 }, { name: 'E-Waste', value: c.eWaste || 0 }, { name: 'Bio-Medical', value: c.bioMedicalWaste || 0 },
    { name: 'Construction', value: c.constructionWaste || 0 }, { name: 'Battery', value: c.batteryWaste || 0 }, { name: 'Radioactive', value: c.radioactiveWaste || 0 },
    { name: 'Other Hazardous', value: c.otherHazardousWaste || 0 }, { name: 'Other Non-Haz', value: c.otherNonHazardousWaste || 0 }
  ].filter(x => x.value > 0)

  const wasteDisposal = [{ name: 'Recycled', value: (c.wasteRecycledPercent || 0) * (c.totalWaste || 0) / 100, color: COLORS.success }, { name: 'Landfill', value: c.landfillVolume || 0, color: COLORS.warning }, { name: 'Incineration', value: c.incinerationVolume || 0, color: COLORS.danger }].filter(x => x.value > 0)

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal company-detail-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <div className="company-header-badge"><Leaf size={20} /></div>
            <div><h2>{c.name}</h2><p>ESG Report FY {c.year} • {c.source_type || 'BRSR'}</p>
              {c.source_url && <a href={c.source_url} target="_blank" rel="noopener noreferrer" className="source-link"><ExternalLink size={14} /> View Source</a>}
            </div>
          </div>
          <button className="modal-close" onClick={onClose}><X size={20} /></button>
        </div>

        {/* Tabs */}
        <div className="tab-bar">
          {['environmental', 'social', 'governance'].map(t => (
            <button key={t} className={`tab-btn ${activeTab === t ? 'active' : ''} ${t}`} onClick={() => setActiveTab(t)}>
              {t === 'environmental' ? <Leaf size={18} /> : t === 'social' ? <Users size={18} /> : <Shield size={18} />}
              <span>{t.charAt(0).toUpperCase() + t.slice(1)}</span>
            </button>
          ))}
        </div>

        <div className="modal-body">
          {/* ENVIRONMENTAL TAB */}
          {activeTab === 'environmental' && (
            <>
              <SectionTitle icon={<Factory size={20} />} title="Climate & Emissions Overview" />
              <div className="metrics-grid-4">
                <MetricCard label="Total Emissions" value={formatLarge(totalEmissions)} unit="tCO2e/year" color="green" />
                <MetricCard label="Reduction Target" value={c.emissionsReductionTarget ? '✓ Set' : 'N/A'} color="blue" />
                <MetricCard label="Net Zero Target" value={c.netZeroTargetYear || 'N/A'} unit="target year" color="purple" />
                <MetricCard label="Intensity (Revenue)" value={c.emissionsIntensityRevenue ? c.emissionsIntensityRevenue.toExponential(2) : 'N/A'} unit="tCO2e/₹" color="orange" />
              </div>

              <div className="charts-row">
                <div className="chart-card">
                  <h4>Emissions by Scope</h4>
                  <div className="chart-small"><ResponsiveContainer>
                    <PieChart><Pie data={scopeData} cx="50%" cy="50%" innerRadius={40} outerRadius={70} dataKey="value" label={({ name, percent }) => `${name}: ${percent}%`}>
                      {[COLORS.scope1, COLORS.scope2, COLORS.scope3].map((c, i) => <Cell key={i} fill={c} />)}
                    </Pie><Tooltip /></PieChart>
                  </ResponsiveContainer></div>
                </div>
                {scope3Categories.length > 0 && <div className="chart-card flex-2">
                  <h4>Scope 3 Category Breakdown</h4>
                  <div className="chart-small"><ResponsiveContainer>
                    <BarChart data={scope3Categories} layout="vertical" margin={{ left: 100 }}>
                      <XAxis type="number" stroke="#64748b" />
                      <YAxis dataKey="name" type="category" stroke="#64748b" width={100} tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', color: '#1e293b' }} />
                      <Bar dataKey="value" fill={COLORS.purple} radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer></div>
                </div>}
              </div>

              <div className="status-cards">
                <StatusCard label="Climate Risk Assessment" value={c.climateRiskAssessment} icon={<AlertTriangle size={16} />} />
                <StatusCard label="Transition Plan" value={c.transitionPlan} icon={<FileText size={16} />} />
                <StatusCard label="Net Zero Commitment" value={c.netZeroCommitment} icon={<Target size={16} />} />
                <StatusCard label="SBTi Status" value={c.sbtiStatus} icon={<Award size={16} />} />
              </div>

              <SectionTitle icon={<Trash2 size={20} />} title="Waste Management" />
              <div className="metrics-grid-4">
                <MetricCard label="Total Waste" value={formatNum(c.totalWaste, 2)} unit="tonnes" color="green" />
                <MetricCard label="Recycled" value={`${c.wasteRecycledPercent || 0}%`} unit="of total" color="blue" />
                <MetricCard label="Hazardous" value={formatNum(c.hazardousWaste, 2)} unit="tonnes" color="red" />
                <MetricCard label="Recycled Content" value={`${c.recycledMaterialContent || 0}%`} unit="in products" color="orange" />
              </div>

              {wasteByCategory.length > 0 && <div className="charts-row">
                <div className="chart-card">
                  <h4>Waste by Category</h4>
                  <div className="chart-small"><ResponsiveContainer>
                    <BarChart data={wasteByCategory}><CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" /><XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={60} /><YAxis stroke="#64748b" /><Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', color: '#1e293b' }} /><Bar dataKey="value" fill={COLORS.purple} radius={[4, 4, 0, 0]} /></BarChart>
                  </ResponsiveContainer></div>
                </div>
                {wasteDisposal.length > 0 && <div className="chart-card">
                  <h4>Waste Disposal Methods</h4>
                  <div className="disposal-bars">{wasteDisposal.map((d, i) => <div key={i} className="disposal-row"><span className="disposal-label">{d.name}</span><div className="disposal-bar-track"><div className="disposal-bar-fill" style={{ width: `${Math.min(100, d.value / Math.max(...wasteDisposal.map(x => x.value)) * 100)}%`, background: d.color }} /></div><span className="disposal-value">{formatNum(d.value, 0)} tonnes</span></div>)}</div>
                </div>}
              </div>}

              <SectionTitle icon={<Droplets size={20} />} title="Water Management" />
              <div className="metrics-grid-5">
                <MetricCard label="Total Withdrawal" value={formatLarge(c.totalWaterWithdrawal)} unit="kilolitres" color="blue" />
                <MetricCard label="Net Consumption" value={formatLarge(c.netWaterConsumption)} unit="kilolitres" color="cyan" />
                <MetricCard label="Recycled" value={`${c.waterRecycledPercent || 0}%`} unit="of total" color="green" />
                <MetricCard label="Stressed Locations" value={c.waterStressedLocations || 'N/A'} color="orange" />
                <MetricCard label="ZLD Status" value={c.zldStatus === 'Yes' ? '✓' : '✗'} />
              </div>

              <SectionTitle icon={<Zap size={20} />} title="Energy" />
              <div className="metrics-grid-4">
                <MetricCard label="Total Energy" value={formatLarge(c.totalEnergy)} unit="GJ" color="orange" />
                <MetricCard label="Renewable %" value={`${c.renewablePercent || 0}%`} color="green" />
                <MetricCard label="Non-Renewable" value={formatLarge(c.totalNonRenewable)} unit="GJ" color="red" />
                <MetricCard label="Renewable" value={formatLarge(c.totalRenewable)} unit="GJ" color="teal" />
              </div>

              <SectionTitle icon={<Scale size={20} />} title="Environmental Governance" />
              <div className="status-cards">
                <StatusCard label="Env Policy" value={c.envPolicy} icon={<FileText size={16} />} />
                <StatusCard label="Green CapEx" value={c.greenCapex ? `${c.greenCapex}%` : 'N/A'} icon={<TrendingUp size={16} />} />
                <StatusCard label="Green R&D" value={c.greenRnD ? `${c.greenRnD}%` : 'N/A'} icon={<Zap size={16} />} />
                <StatusCard label="Fines/Penalties" value={c.envFines === 0 ? '₹0' : c.envFines ? `₹${formatNum(c.envFines)}` : 'N/A'} icon={<AlertTriangle size={16} />} />
                <StatusCard label="Supplier Reqs" value={c.supplierEnvReqs} icon={<Check size={16} />} />
              </div>
            </>
          )}

          {/* SOCIAL TAB */}
          {activeTab === 'social' && (
            <>
              <SectionTitle icon={<Users size={20} />} title="Workforce Overview" />
              <div className="metrics-grid-4">
                <MetricCard label="Total Workforce" value={formatLarge(c.totalWorkforce)} icon={<Users size={18} />} color="blue" />
                <MetricCard label="Training Hours" value={c.trainingHours || 'N/A'} icon={<Briefcase size={18} />} color="purple" />
                <MetricCard label="Supplier Audits" value={c.supplierSocialAudits || 'N/A'} icon={<Check size={18} />} color="orange" />
              </div>

              <SectionTitle icon={<Users size={20} />} title="Gender Diversity" />
              <div className="diversity-cards">
                <div className="diversity-card pink"><div className="diversity-label">Board</div><div className="diversity-value">{c.genderDiversityBoard || 0}%</div><div className="diversity-sub">Female representation</div></div>
                <div className="diversity-card purple"><div className="diversity-label">Permanent Employees</div><div className="diversity-value">{c.genderDiversityPermEmp || 0}%</div><div className="diversity-sub">Female representation</div></div>
                <div className="diversity-card blue"><div className="diversity-label">Total Employees</div><div className="diversity-value">{c.genderDiversityTotal || 0}%</div><div className="diversity-sub">Female representation</div></div>
              </div>

              <SectionTitle icon={<TrendingUp size={20} />} title="Attrition Rates" />
              <div className="attrition-section">
                <div className="attrition-chart"><ResponsiveContainer>
                  <BarChart data={[{ name: 'Employees', value: c.attritionEmployees || 0 }, { name: 'Workers', value: typeof c.attritionWorkers === 'number' ? c.attritionWorkers : 0 }]}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" /><XAxis dataKey="name" stroke="#64748b" /><YAxis stroke="#64748b" />
                    <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', color: '#1e293b' }} />
                    <Bar dataKey="value" fill={COLORS.warning} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer></div>
                <div className="attrition-cards">
                  <div className="attrition-card orange"><div className="attrition-label">Employee Attrition</div><div className="attrition-value">{c.attritionEmployees || 0}%</div><div className="attrition-bar"><div style={{ width: `${Math.min(100, c.attritionEmployees || 0)}%`, background: COLORS.warning }} /></div></div>
                  <div className="attrition-card red"><div className="attrition-label">Worker Attrition</div><div className="attrition-value">{typeof c.attritionWorkers === 'number' ? c.attritionWorkers : c.attritionWorkers || 'N/A'}%</div><div className="attrition-bar"><div style={{ width: `${Math.min(100, typeof c.attritionWorkers === 'number' ? c.attritionWorkers : 0)}%`, background: COLORS.danger }} /></div></div>
                </div>
              </div>

              <SectionTitle icon={<Shield size={20} />} title="Safety Performance (LTIFR)" />
              <div className="safety-section">
                <div className="safety-chart"><ResponsiveContainer>
                  <BarChart data={[{ name: 'Employees', value: c.ltifrEmployees || 0 }, { name: 'Workers', value: c.ltifrWorkers || 0 }]}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" /><XAxis dataKey="name" stroke="#64748b" /><YAxis stroke="#64748b" />
                    <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', color: '#1e293b' }} />
                    <Bar dataKey="value" fill={COLORS.danger} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer></div>
                <div className="safety-cards">
                  <div className="safety-card green"><div className="safety-label">Employees LTIFR</div><div className="safety-value">{c.ltifrEmployees || 0}</div><div className="safety-status">{c.ltifrEmployees === 0 ? '✓ Excellent' : '⚠ Monitor'}</div></div>
                  <div className="safety-card green"><div className="safety-label">Workers LTIFR</div><div className="safety-value">{c.ltifrWorkers || 0}</div><div className="safety-status">{c.ltifrWorkers === 0 ? '✓ Excellent' : '⚠ Monitor'}</div></div>
                </div>
              </div>

              <div className="status-cards">
                <StatusCard label="ISO 45001" value={c.iso45001} icon={<Award size={16} />} />
                <StatusCard label="Human Rights Policy" value={c.humanRightsPolicy} icon={<FileText size={16} />} />
              </div>
            </>
          )}

          {/* GOVERNANCE TAB */}
          {activeTab === 'governance' && (
            <>
              <SectionTitle icon={<Shield size={20} />} title="Governance Overview" />
              <div className="status-cards large">
                <StatusCard label="Anti-Corruption Policy" value={c.antiCorruptionPolicy} icon={<Shield size={18} />} large />
                <StatusCard label="Whistleblower Mechanism" value={c.whistleblowerMechanism} icon={<AlertTriangle size={18} />} large />
                <StatusCard label="ESG Oversight" value={c.esgOversightCommittee} icon={<Users size={18} />} large />
                <StatusCard label="Board Independence" value={c.boardIndependence} icon={<Scale size={18} />} large />
                <StatusCard label="ESG Linked Pay" value={c.esgLinkedPay} icon={<TrendingUp size={18} />} large />
                <StatusCard label="Legal Cases" value={c.legalCases} icon={<FileText size={18} />} large />
              </div>

              <SectionTitle icon={<Award size={20} />} title="External Ratings & Certifications" />
              <div className="ratings-grid">
                <RatingCard label="CDP Score" value={c.cdpScore} />
                <RatingCard label="DJSI Inclusion" value={c.djsiInclusion} />
                <RatingCard label="EcoVadis Medal" value={c.ecoVadisMedal} />
                <RatingCard label="MSCI Rating" value={c.msciRating} />
                <RatingCard label="Sustainalytics" value={c.sustainalyticsScore} />
                <RatingCard label="UNGC Participant" value={c.ungcParticipant} />
              </div>

              <SectionTitle icon={<Award size={20} />} title="Certifications" />
              <div className="cert-grid">
                <CertCard label="ISO 14001" value={c.iso14001} />
                <CertCard label="ISO 45001" value={c.iso45001} />
                <CertCard label="ISO 50001" value={c.iso50001} />
                <CertCard label="CPCB Compliance" value={c.cpcbCompliance} />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function SectionTitle({ icon, title }) {
  return <div className="section-title">{icon}<span>{title}</span></div>
}

function MetricCard({ label, value, unit, color, icon }) {
  return <div className={`metric-card ${color || ''}`}>{icon && <div className="metric-icon">{icon}</div>}<div className="metric-label">{label}</div><div className="metric-value">{value}</div>{unit && <div className="metric-unit">{unit}</div>}</div>
}

function StatusCard({ label, value, icon, large }) {
  const isPositive = value && (value === 'Yes' || value === 'Done' || value === 'Published' || value === 'Committed' || value.includes?.('✓') || value === '0' || value === '₹0')
  const displayValue = value === null || value === undefined || value === '' || value === 'Not Disclosed' ? 'N/A' : value === 'Yes' ? '✓ Yes' : value === 'No' ? '✗ No' : value
  return <div className={`status-card ${large ? 'large' : ''} ${isPositive ? 'positive' : displayValue === 'N/A' ? 'neutral' : 'neutral'}`}><div className="status-icon">{icon}</div><div className="status-label">{label}</div><div className="status-value">{displayValue}</div></div>
}

function RatingCard({ label, value }) {
  return <div className="rating-card"><div className="rating-label">{label}</div><div className="rating-value">{value || 'Not Disclosed'}</div></div>
}

function CertCard({ label, value }) {
  const isYes = value === 'Yes'
  return <div className={`cert-card ${isYes ? 'certified' : 'not-certified'}`}><div className="cert-icon">{isYes ? <Check size={24} /> : <X size={24} />}</div><div className="cert-label">{label}</div><div className="cert-status">{isYes ? 'Certified' : 'Not Certified'}</div></div>
}

export default App
