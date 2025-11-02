import React, { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';

export default function MOTLandingPage() {
  const [showAdvancedInfo, setShowAdvancedInfo] = useState(false);

  return (
    <>
      <Head>
        <title>Malaysia On Track (MOT) - Malaysia Swimming Analytics</title>
        <meta name="description" content="Malaysia On Track developmental pathway for elite swimmers" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div style={{ 
        fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        fontSize: '16px',
        minHeight: '100vh',
        width: '100%',
        backgroundColor: '#f5f5f5',
        padding: '20px',
        boxSizing: 'border-box'
      }}>
        {/* Header */}
        <div style={{ 
          textAlign: 'center', 
          marginBottom: '30px',
          backgroundColor: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h1 style={{ 
            fontSize: '2rem', 
            margin: '0 0 10px 0',
            color: '#2c3e50',
            borderBottom: '3px solid #cc0000',
            paddingBottom: '10px',
            display: 'inline-block'
          }}>
            <img src="/mas-logo.png" alt="MAS Logo" style={{ height: '1em', verticalAlign: 'middle', margin: '0 8px' }} />
            Malaysia On Track (MOT)
            <img src="/mas-logo.png" alt="MAS Logo" style={{ height: '1em', verticalAlign: 'middle', margin: '0 8px' }} />
          </h1>
          <p style={{ margin: '10px 0 0 0', color: '#666', fontSize: '1.1rem' }}>
            Developmental Pathway for Elite Swimmers
          </p>
          <Link href="/" style={{ 
            display: 'inline-block', 
            marginTop: '15px',
            color: '#cc0000',
            textDecoration: 'none',
            fontSize: '0.9rem'
          }}>
            ← Back to Times Database
          </Link>
        </div>

        <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
          {/* Overview Section */}
          <section style={{ 
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            marginBottom: '20px'
          }}>
            <h2 style={{ 
              color: '#2c3e50',
              marginTop: '0',
              marginBottom: '20px',
              fontSize: '1.8rem',
              borderLeft: '5px solid #cc0000',
              paddingLeft: '15px'
            }}>
              What is MOT?
            </h2>
            
            <p style={{ lineHeight: '1.8', marginBottom: '15px', fontSize: '1.1rem' }}>
              <strong>Malaysia On Track (MOT)</strong> is a data-driven pathway designed to identify and support swimmers with the highest potential to deliver international medals for Malaysia. Based on Canada's successful "On Track" methodology, MOT provides age-specific progression benchmarks from entry age (15) to arrival age (25).
            </p>

            <div style={{
              backgroundColor: '#e8f4f8',
              borderLeft: '5px solid #3498db',
              padding: '20px',
              margin: '20px 0',
              borderRadius: '4px'
            }}>
              <h3 style={{ marginTop: '0', color: '#2c3e50' }}>Key Purpose:</h3>
              <ul style={{ lineHeight: '1.8', marginBottom: '0' }}>
                <li><strong>Medal Potential Identification:</strong> Identify swimmers with verified medal potential</li>
                <li><strong>Development Pathway:</strong> Track progression from age 15 to 25</li>
                <li><strong>Resource Allocation:</strong> Guide funding to athletes with highest medal potential</li>
                <li><strong>Performance Benchmarking:</strong> Compare swimmers against international progression standards</li>
              </ul>
            </div>
          </section>

          {/* How MOT Times Are Calculated */}
          <section style={{ 
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            marginBottom: '20px'
          }}>
            <h2 style={{ 
              color: '#2c3e50',
              marginTop: '0',
              marginBottom: '20px',
              fontSize: '1.8rem',
              borderLeft: '5px solid #cc0000',
              paddingLeft: '15px'
            }}>
              How Are MOT Times Determined?
            </h2>

            <div style={{ lineHeight: '1.8' }}>
              <p style={{ marginBottom: '20px', fontSize: '1.05rem' }}>
                MOT progression times are calculated using a comprehensive statistical analysis of elite swimming development patterns:
              </p>

              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '20px',
                marginBottom: '25px'
              }}>
                <div style={{
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  padding: '20px',
                  backgroundColor: '#fafafa'
                }}>
                  <h3 style={{ marginTop: '0', color: '#cc0000', fontSize: '1.2rem' }}>1. Data Foundation</h3>
                  <p style={{ marginBottom: '0', fontSize: '0.95rem' }}>
                    Analysis of <strong>top 500 elite swimmers</strong> per event/gender/age from USA Swimming season rankings (2021-2025), representing approximately <strong>7-12%</strong> of all competitive swimmers.
                  </p>
                </div>

                <div style={{
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  padding: '20px',
                  backgroundColor: '#fafafa'
                }}>
                  <h3 style={{ marginTop: '0', color: '#cc0000', fontSize: '1.2rem' }}>2. Improvement Analysis</h3>
                  <p style={{ marginBottom: '0', fontSize: '0.95rem' }}>
                    Statistical analysis of improvement rates across <strong>84 age transitions</strong> (14 events × 2 genders × 3 transitions: 15→16, 16→17, 17→18).
                  </p>
                </div>

                <div style={{
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  padding: '20px',
                  backgroundColor: '#fafafa'
                }}>
                  <h3 style={{ marginTop: '0', color: '#cc0000', fontSize: '1.2rem' }}>3. International Comparison</h3>
                  <p style={{ marginBottom: '0', fontSize: '0.95rem' }}>
                    Comparison with <strong>Canada On Track</strong> reference times (Track 1, 2, 3) to validate progression curves and account for different developmental timelines.
                  </p>
                </div>

                <div style={{
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  padding: '20px',
                  backgroundColor: '#fafafa'
                }}>
                  <h3 style={{ marginTop: '0', color: '#cc0000', fontSize: '1.2rem' }}>4. Progression Curve</h3>
                  <p style={{ marginBottom: '0', fontSize: '0.95rem' }}>
                    Development of age-specific progression curves anchored to SEA Games bronze medal times as arrival benchmarks (age 25).
                  </p>
                </div>
              </div>

              <div style={{
                backgroundColor: '#fff3cd',
                borderLeft: '5px solid #f39c12',
                padding: '20px',
                marginTop: '20px',
                borderRadius: '4px'
              }}>
                <p style={{ margin: '0', fontSize: '1rem' }}>
                  <strong>💡 Important:</strong> MOT focuses on the <strong>elite portion</strong> of competitive swimmers. The data represents top performers only, which is exactly what we need for setting elite developmental standards.
                </p>
              </div>
            </div>
          </section>

          {/* Access Section */}
          <section style={{ 
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            marginBottom: '20px'
          }}>
            <h2 style={{ 
              color: '#2c3e50',
              marginTop: '0',
              marginBottom: '20px',
              fontSize: '1.8rem',
              borderLeft: '5px solid #cc0000',
              paddingLeft: '15px'
            }}>
              Access MOT Tools
            </h2>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '20px'
            }}>
              <div style={{
                border: '2px solid #cc0000',
                borderRadius: '8px',
                padding: '25px',
                textAlign: 'center',
                backgroundColor: '#fff',
                transition: 'transform 0.2s, box-shadow 0.2s',
                cursor: 'pointer'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-5px)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(204, 0, 0, 0.2)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}>
                <div style={{ fontSize: '3rem', marginBottom: '10px' }}>📊</div>
                <h3 style={{ margin: '0 0 10px 0', color: '#2c3e50', fontSize: '1.3rem' }}>
                  View MOT Tables
                </h3>
                <p style={{ margin: '0 0 15px 0', color: '#666', fontSize: '0.95rem' }}>
                  Browse the complete MOT progression times for all events and ages
                </p>
                <button style={{
                  backgroundColor: '#cc0000',
                  color: 'white',
                  border: 'none',
                  padding: '10px 20px',
                  borderRadius: '5px',
                  fontSize: '1rem',
                  cursor: 'pointer',
                  fontWeight: '600'
                }}>
                  Coming Soon
                </button>
                <p style={{ margin: '10px 0 0 0', fontSize: '0.85rem', color: '#999' }}>
                  (Feature in development)
                </p>
              </div>

              <div style={{
                border: '2px solid #cc0000',
                borderRadius: '8px',
                padding: '25px',
                textAlign: 'center',
                backgroundColor: '#fff',
                transition: 'transform 0.2s, box-shadow 0.2s',
                cursor: 'pointer'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-5px)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(204, 0, 0, 0.2)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}>
                <div style={{ fontSize: '3rem', marginBottom: '10px' }}>📈</div>
                <h3 style={{ margin: '0 0 10px 0', color: '#2c3e50', fontSize: '1.3rem' }}>
                  Personal Progress Tracker
                </h3>
                <p style={{ margin: '0 0 15px 0', color: '#666', fontSize: '0.95rem' }}>
                  Generate a personalized graph showing your progression vs. MOT benchmarks
                </p>
                <button style={{
                  backgroundColor: '#cc0000',
                  color: 'white',
                  border: 'none',
                  padding: '10px 20px',
                  borderRadius: '5px',
                  fontSize: '1rem',
                  cursor: 'pointer',
                  fontWeight: '600'
                }}>
                  Coming Soon
                </button>
                <p style={{ margin: '10px 0 0 0', fontSize: '0.85rem', color: '#999' }}>
                  (Feature in development)
                </p>
              </div>
            </div>
          </section>

          {/* Learn More Section */}
          <section style={{ 
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            marginBottom: '20px'
          }}>
            <h2 style={{ 
              color: '#2c3e50',
              marginTop: '0',
              marginBottom: '20px',
              fontSize: '1.8rem',
              borderLeft: '5px solid #cc0000',
              paddingLeft: '15px'
            }}>
              Learn More About MOT
            </h2>

            <p style={{ lineHeight: '1.8', marginBottom: '20px', fontSize: '1.05rem' }}>
              For those interested in understanding the detailed methodology and statistical foundation behind MOT:
            </p>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '15px'
            }}>
              <a 
                href="../../statistical_analysis/reports/MOT_Data_Methodology_and_Assumptions.html"
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'block',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  padding: '20px',
                  textDecoration: 'none',
                  color: 'inherit',
                  backgroundColor: '#fafafa',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#e8f4f8';
                  e.currentTarget.style.borderColor = '#3498db';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#fafafa';
                  e.currentTarget.style.borderColor = '#ddd';
                }}
              >
                <h3 style={{ margin: '0 0 10px 0', color: '#2c3e50', fontSize: '1.2rem' }}>
                  📋 Data Characteristics & Assumptions
                </h3>
                <p style={{ margin: '0', color: '#666', fontSize: '0.95rem' }}>
                  Understand the nature of our data, distribution characteristics, and sampling methodology
                </p>
              </a>

              <a 
                href="file:///C:/Users/megan/OneDrive/Documents/Malaysia%20Swimming%20Analytics/statistical_analysis/MOT_Delta_Analysis_Index.html"
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'block',
                  border: '2px solid #cc0000',
                  borderRadius: '8px',
                  padding: '25px',
                  textDecoration: 'none',
                  color: 'inherit',
                  backgroundColor: '#fff',
                  transition: 'all 0.2s',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#fff3f3';
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(204, 0, 0, 0.2)';
                  e.currentTarget.style.transform = 'translateY(-3px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#fff';
                  e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <h3 style={{ margin: '0 0 10px 0', color: '#cc0000', fontSize: '1.4rem', fontWeight: 'bold' }}>
                  📊 MOT Data Analysis Portal
                </h3>
                <p style={{ margin: '0', color: '#666', fontSize: '1rem', lineHeight: '1.6' }}>
                  Access the comprehensive statistical analysis: 84 improvement analyses, raw data for ages 15-18, USA vs Canada comparisons, and detailed methodology
                </p>
                <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#f0f0f0', borderRadius: '4px', fontSize: '0.9rem', color: '#333' }}>
                  <strong>Click here to explore:</strong> Raw data, improvement statistics, z-score analysis, and complete methodology
                </div>
              </a>

              <a 
                href="../../statistical_analysis/reports/Delta_Comparison_USA_vs_Canada.html"
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'block',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  padding: '20px',
                  textDecoration: 'none',
                  color: 'inherit',
                  backgroundColor: '#fafafa',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#e8f4f8';
                  e.currentTarget.style.borderColor = '#3498db';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#fafafa';
                  e.currentTarget.style.borderColor = '#ddd';
                }}
              >
                <h3 style={{ margin: '0 0 10px 0', color: '#2c3e50', fontSize: '1.2rem' }}>
                  📈 USA vs Canada Delta Comparison
                </h3>
                <p style={{ margin: '0', color: '#666', fontSize: '0.95rem' }}>
                  Detailed comparison of USA median improvement deltas with Canada On Track reference times
                </p>
              </a>
            </div>
          </section>

          {/* Age Range Information */}
          <section style={{ 
            backgroundColor: '#e8f4f8',
            padding: '25px',
            borderRadius: '8px',
            marginBottom: '20px',
            borderLeft: '5px solid #3498db'
          }}>
            <h3 style={{ marginTop: '0', color: '#2c3e50', fontSize: '1.3rem' }}>
              Age Range: 15 to 25
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
              <div>
                <strong style={{ color: '#2c3e50' }}>Entry Age: 15</strong>
                <ul style={{ marginTop: '5px', lineHeight: '1.6' }}>
                  <li>Physical maturity has evened out</li>
                  <li>Training becomes the main driver</li>
                  <li>Performance tracking becomes predictive</li>
                </ul>
              </div>
              <div>
                <strong style={{ color: '#2c3e50' }}>Arrival Age: 25</strong>
                <ul style={{ marginTop: '5px', lineHeight: '1.6' }}>
                  <li>Typical age for international medal success</li>
                  <li>Development window closes statistically</li>
                  <li>Extended support through critical years</li>
                </ul>
              </div>
            </div>
          </section>
        </div>

        {/* Footer */}
        <div style={{
          textAlign: 'center',
          marginTop: '40px',
          padding: '20px',
          color: '#666',
          fontSize: '0.9rem'
        }}>
          <p style={{ margin: '0' }}>
            Malaysia On Track (MOT) - Based on Canada's successful On Track methodology
          </p>
          <p style={{ margin: '5px 0 0 0', fontSize: '0.85rem' }}>
            Data sources: USA Swimming (2021-2025), Canada On Track (April 2025)
          </p>
        </div>
      </div>
    </>
  );
}

