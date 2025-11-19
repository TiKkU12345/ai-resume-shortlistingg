"""
AI Resume Shortlisting - Web Interface using Streamlit
Beautiful, interactive dashboard for resume screening and ranking
"""

import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from resume_parser import ResumeParser
from job_resume_matcher import CandidateRanker, JobDescriptionParser
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AI Resume Shortlisting System",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .candidate-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        background-color: #ffffff;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
    }
    .score-excellent {
        color: #10b981;
        font-weight: bold;
    }
    .score-good {
        color: #f59e0b;
        font-weight: bold;
    }
    .score-moderate {
        color: #ef4444;
        font-weight: bold;
    }
    h1 {
        color: #1e3a8a;
    }
    </style>
""", unsafe_allow_html=True)

class ResumeShortlistingApp:
    """Main application class for the web interface"""
    
    def __init__(self):
        self.parser = ResumeParser()
        self.ranker = CandidateRanker()
        self.job_parser = JobDescriptionParser()
        
        # Initialize session state
        if 'parsed_resumes' not in st.session_state:
            st.session_state.parsed_resumes = []
        if 'ranked_candidates' not in st.session_state:
            st.session_state.ranked_candidates = []
        if 'job_description' not in st.session_state:
            st.session_state.job_description = ""
    
    def run(self):
        """Main application runner"""
        # Header
        st.title("🎯 AI Resume Shortlisting System")
        st.markdown("**Intelligent Resume Screening powered by Machine Learning**")
        st.markdown("---")
        
        # Sidebar
        self.render_sidebar()
        
        # Main content based on selected page
        page = st.session_state.get('page', 'Upload Resumes')
        
        if page == 'Upload Resumes':
            self.page_upload_resumes()
        elif page == 'Job Description':
            self.page_job_description()
        elif page == 'Rankings':
            self.page_rankings()
        elif page == 'Analytics':
            self.page_analytics()
    
    def render_sidebar(self):
        """Render sidebar navigation"""
        with st.sidebar:
            st.image("https://via.placeholder.com/200x80/667eea/ffffff?text=AI+Recruiter", 
        use_container_width=True)
            
            
            st.markdown("---")
            
            # Navigation
            st.header("📋 Navigation")
            page = st.radio(
                "Go to:",
                ["Upload Resumes", "Job Description", "Rankings", "Analytics"],
                key='page'
            )
            
            st.markdown("---")
            
            # Statistics
            st.header("📊 Statistics")
            st.metric("Resumes Uploaded", len(st.session_state.parsed_resumes))
            
            if st.session_state.ranked_candidates:
                excellent = sum(1 for c in st.session_state.ranked_candidates 
                              if c['overall_score'] >= 80)
                st.metric("Excellent Matches", excellent)
            
            st.markdown("---")
            
            # Clear data button
            if st.button("🗑️ Clear All Data", use_container_width=True):
                st.session_state.parsed_resumes = []
                st.session_state.ranked_candidates = []
                st.session_state.job_description = ""
                st.success("Data cleared!")
                st.rerun()
    
    def page_upload_resumes(self):
        """Resume upload and parsing page"""
        st.header("📤 Upload & Parse Resumes")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Upload Resume Files")
            st.markdown("Supported formats: **PDF, DOCX**")
            
            # File uploader
            uploaded_files = st.file_uploader(
                "Choose resume files",
                type=['pdf', 'docx'],
                accept_multiple_files=True,
                help="Upload one or more resume files to parse"
            )
            
            if uploaded_files:
                if st.button("🔍 Parse All Resumes", type="primary", use_container_width=True):
                    self.parse_uploaded_files(uploaded_files)
        
        with col2:
            st.markdown("### Quick Stats")
            st.info(f"**Total Resumes:** {len(st.session_state.parsed_resumes)}")
            
            if st.session_state.parsed_resumes:
                avg_exp = sum(r.get('total_experience_years', 0) 
                            for r in st.session_state.parsed_resumes) / len(st.session_state.parsed_resumes)
                st.info(f"**Avg Experience:** {avg_exp:.1f} years")
        
        # Display parsed resumes
        if st.session_state.parsed_resumes:
            st.markdown("---")
            st.markdown("### 📋 Parsed Resumes")
            
            self.display_parsed_resumes()
    
    def parse_uploaded_files(self, uploaded_files):
        """Parse uploaded resume files"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        parsed_count = 0
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Parsing: {uploaded_file.name}")
            
            try:
                # Save file temporarily
                temp_path = f"temp_{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Parse resume
                resume_data = self.parser.parse_resume(temp_path)
                resume_data['filename'] = uploaded_file.name
                
                # Add to session state
                st.session_state.parsed_resumes.append(resume_data)
                parsed_count += 1
                
                # Clean up temp file
                os.remove(temp_path)
                
            except Exception as e:
                st.error(f"Failed to parse {uploaded_file.name}: {str(e)}")
            
            # Update progress
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        status_text.empty()
        progress_bar.empty()
        
        st.success(f"✅ Successfully parsed {parsed_count}/{len(uploaded_files)} resumes!")
        st.rerun()
    
    def display_parsed_resumes(self):
        """Display list of parsed resumes"""
        for i, resume in enumerate(st.session_state.parsed_resumes):
            with st.expander(f"📄 {resume['contact'].get('name', 'Unknown')} - {resume.get('filename', '')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**Contact Info**")
                    st.write(f"📧 {resume['contact'].get('email', 'N/A')}")
                    st.write(f"📱 {resume['contact'].get('phone', 'N/A')}")
                    st.write(f"💼 {resume['contact'].get('linkedin', 'N/A')}")
                
                with col2:
                    st.markdown("**Experience**")
                    st.write(f"⏱️ {resume.get('total_experience_years', 0)} years")
                    st.write(f"💼 {len(resume.get('experience', []))} jobs")
                    st.write(f"🎓 {len(resume.get('education', []))} degrees")
                
                with col3:
                    st.markdown("**Skills**")
                    total_skills = sum(len(v) for v in resume.get('skills', {}).values())
                    st.write(f"🛠️ {total_skills} skills")
                    
                    # Show top skills
                    all_skills = []
                    for skills in resume.get('skills', {}).values():
                        all_skills.extend(skills)
                    if all_skills:
                        st.write(f"Top: {', '.join(all_skills[:3])}")
                
                # Delete button
                if st.button(f"🗑️ Remove", key=f"remove_{i}"):
                    st.session_state.parsed_resumes.pop(i)
                    st.rerun()
    
    def page_job_description(self):
        """Job description input page"""
        st.header("📝 Job Description")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Enter Job Requirements")
            
            # Job description input
            job_description = st.text_area(
                "Paste the complete job description here:",
                value=st.session_state.job_description,
                height=400,
                placeholder="""Example:
Senior Python Developer

Requirements:
- 3-5 years of Python experience
- Machine Learning expertise
- AWS/Cloud experience
- Bachelor's in Computer Science

Must Have Skills:
- Python, TensorFlow, SQL, REST API

Nice to Have:
- Docker, Kubernetes, React
""",
                help="Include requirements, skills, experience, and responsibilities"
            )
            
            st.session_state.job_description = job_description
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("✨ Use Sample Job", use_container_width=True):
                    st.session_state.job_description = self.get_sample_job_description()
                    st.rerun()
            
            with col_btn2:
                if st.button("🚀 Match Candidates", type="primary", use_container_width=True):
                    if not st.session_state.parsed_resumes:
                        st.error("Please upload resumes first!")
                    elif not job_description.strip():
                        st.error("Please enter a job description!")
                    else:
                        self.match_candidates(job_description)
        
        with col2:
            if job_description:
                st.markdown("### 🔍 Job Analysis")
                
                # Parse and display job info
                job_data = self.job_parser.parse_job_description(job_description)
                
                st.info(f"**Position:** {job_data['title']}")
                st.info(f"**Min Experience:** {job_data['min_experience']} years")
                
                if job_data['required_skills']:
                    with st.expander("Required Skills"):
                        for skill in job_data['required_skills'][:10]:
                            st.write(f"• {skill}")
                
                if job_data['preferred_skills']:
                    with st.expander("Preferred Skills"):
                        for skill in job_data['preferred_skills'][:10]:
                            st.write(f"• {skill}")
    
    def match_candidates(self, job_description):
        """Match candidates with job description"""
        with st.spinner("🤖 AI is analyzing candidates..."):
            try:
                ranked = self.ranker.rank_candidates(
                    st.session_state.parsed_resumes,
                    job_description
                )
                st.session_state.ranked_candidates = ranked
                st.success(f"✅ Ranked {len(ranked)} candidates!")
                
                # Switch to rankings page
                st.session_state.page = 'Rankings'
                st.rerun()
                
            except Exception as e:
                st.error(f"Matching failed: {str(e)}")
    
    def page_rankings(self):
        """Display ranked candidates"""
        st.header("🏆 Candidate Rankings")
        
        if not st.session_state.ranked_candidates:
            st.warning("⚠️ No rankings yet! Please match candidates with a job description first.")
            return
        
        # Summary metrics
        self.display_ranking_metrics()
        
        st.markdown("---")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_score = st.slider("Minimum Score", 0, 100, 0, 5)
        
        with col2:
            sort_by = st.selectbox("Sort By", ["Overall Score", "Skills Score", "Experience Score"])
        
        with col3:
            max_candidates = len(st.session_state.ranked_candidates)
            default_count = min(5, max_candidates)
            show_count = st.number_input("Show Top N", 1, max_candidates, default_count)
        
        # Filter and sort
        filtered = [c for c in st.session_state.ranked_candidates if c['overall_score'] >= min_score]
        
        if sort_by == "Skills Score":
            filtered.sort(key=lambda x: x['skills_score'], reverse=True)
        elif sort_by == "Experience Score":
            filtered.sort(key=lambda x: x['experience_score'], reverse=True)
        
        filtered = filtered[:show_count]
        
        st.markdown(f"### Showing {len(filtered)} Candidates")
        
        # Display candidates
        for i, candidate in enumerate(filtered, 1):
            self.display_candidate_card(i, candidate)
        
        # Export options
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Download Report (JSON)", use_container_width=True):
                self.download_json_report()
        
        with col2:
            if st.button("📊 Download Report (CSV)", use_container_width=True):
                self.download_csv_report()
    def display_ranking_metrics(self):
        """Display summary metrics for rankings"""
        col1, col2, col3, col4 = st.columns(4)
        
        candidates = st.session_state.ranked_candidates
        
        with col1:
            st.metric("Total Candidates", len(candidates))
        
        with col2:
            excellent = sum(1 for c in candidates if c['overall_score'] >= 80)
            st.metric("Excellent Match (80%+)", excellent)
        
        with col3:
            good = sum(1 for c in candidates if 60 <= c['overall_score'] < 80)
            st.metric("Good Match (60-79%)", good)
        
        with col4:
            if candidates:
                avg_score = sum(c['overall_score'] for c in candidates) / len(candidates)
                st.metric("Average Score", f"{avg_score:.1f}%")
    
    def display_candidate_card(self, rank, candidate):
        """Display individual candidate card"""
        score = candidate['overall_score']
        
        # Determine score class
        if score >= 80:
            score_class = "score-excellent"
            emoji = "🟢"
            status = "EXCELLENT MATCH"
        elif score >= 60:
            score_class = "score-good"
            emoji = "🟡"
            status = "GOOD MATCH"
        else:
            score_class = "score-moderate"
            emoji = "🟠"
            status = "MODERATE MATCH"
        
        with st.expander(f"{emoji} **RANK #{rank}: {candidate['name']}** - {score:.1f}% ({status})", expanded=(rank <= 3)):
            # Basic info
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**📧 Email:** {candidate['email']}")
                st.markdown(f"**📱 Phone:** {candidate['phone']}")
                st.markdown(f"**⏱️ Experience:** {candidate['total_experience']} years")
            
            with col2:
                st.markdown("**Overall Score**")
                st.markdown(f"<h1 class='{score_class}'>{score:.1f}%</h1>", unsafe_allow_html=True)
            
            # Score breakdown
            st.markdown("---")
            st.markdown("### 📊 Score Breakdown")
            
            scores_df = pd.DataFrame({
                'Category': ['Skills', 'Experience', 'Education'],
                'Score': [
                    candidate['skills_score'],
                    candidate['experience_score'],
                    candidate['education_score']
                ]
            })
            
            fig = px.bar(
                scores_df,
                x='Category',
                y='Score',
                color='Score',
                color_continuous_scale='RdYlGn',
                range_color=[0, 100]
            )
            fig.update_layout(height=250, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, key=f"score_chart_rank_{rank}")
            
            # Skills analysis
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ✅ Matched Skills")
                if candidate['matched_skills']:
                    for skill in candidate['matched_skills'][:10]:
                        st.markdown(f"✓ {skill}")
                    if len(candidate['matched_skills']) > 10:
                        st.markdown(f"*+{len(candidate['matched_skills']) - 10} more*")
                else:
                    st.markdown("*No exact skill matches*")
            
            with col2:
                st.markdown("### ❌ Missing Skills")
                if candidate['missing_skills']:
                    for skill in candidate['missing_skills'][:10]:
                        st.markdown(f"✗ {skill}")
                    if len(candidate['missing_skills']) > 10:
                        st.markdown(f"*+{len(candidate['missing_skills']) - 10} more*")
                else:
                    st.markdown("*All required skills present*")
            
            # Explanation
            st.markdown("---")
            st.markdown("### 💡 Assessment")
            
            exp = candidate['explanation']
            st.info(exp['summary'])
            
            if exp['strengths']:
                st.markdown("**Strengths:**")
                for strength in exp['strengths']:
                    st.markdown(f"• {strength}")
            
            if exp['weaknesses']:
                st.markdown("**Weaknesses:**")
                for weakness in exp['weaknesses']:
                    st.markdown(f"• {weakness}")
            
            if exp['recommendations']:
                st.markdown("**Recommendation:**")
                for rec in exp['recommendations']:
                    st.success(rec)

    def page_analytics(self):
        """Analytics and insights page"""
        st.header("📈 Analytics & Insights")
        
        if not st.session_state.ranked_candidates:
            st.warning("No data to analyze. Please rank candidates first!")
            return
        
        candidates = st.session_state.ranked_candidates
        
        # Score distribution
        st.markdown("### Score Distribution")
        
        scores = [c['overall_score'] for c in candidates]
        fig = go.Figure(data=[go.Histogram(x=scores, nbinsx=10, marker_color='#667eea')])
        fig.update_layout(
            title="Candidate Score Distribution",
            xaxis_title="Overall Score",
            yaxis_title="Number of Candidates",
            height=350
        )
        st.plotly_chart(fig, use_container_width=True, key="score_distribution")
        
        # Skills analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Most Common Skills")
            all_matched_skills = []
            for c in candidates:
                all_matched_skills.extend(c['matched_skills'])
            
            if all_matched_skills:
                skills_count = pd.Series(all_matched_skills).value_counts().head(10)
                fig = px.bar(
                    x=skills_count.values,
                    y=skills_count.index,
                    orientation='h',
                    labels={'x': 'Count', 'y': 'Skill'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True, key="common_skills")
        
        with col2:
            st.markdown("### Most Missing Skills")
            all_missing_skills = []
            for c in candidates:
                all_missing_skills.extend(c['missing_skills'])
            
            if all_missing_skills:
                missing_count = pd.Series(all_missing_skills).value_counts().head(10)
                fig = px.bar(
                    x=missing_count.values,
                    y=missing_count.index,
                    orientation='h',
                    labels={'x': 'Count', 'y': 'Skill'},
                    color_discrete_sequence=['#ef4444']
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True, key="missing_skills")
        
        # Experience vs Score
        st.markdown("### Experience vs Match Score")
        
        exp_data = pd.DataFrame({
            'Experience': [c['total_experience'] for c in candidates],
            'Score': [c['overall_score'] for c in candidates],
            'Name': [c['name'] for c in candidates]
        })
        
        fig = px.scatter(
            exp_data,
            x='Experience',
            y='Score',
            hover_data=['Name'],
            size=[10]*len(exp_data),
            color='Score',
            color_continuous_scale='RdYlGn'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True, key="exp_vs_score")
    
    def download_json_report(self):
        """Generate JSON report for download"""
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'total_candidates': len(st.session_state.ranked_candidates),
            'candidates': st.session_state.ranked_candidates
        }
        
        json_str = json.dumps(report_data, indent=2)
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name=f"ranking_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def download_csv_report(self):
        """Generate CSV report for download"""
        candidates = st.session_state.ranked_candidates
        
        csv_data = []
        for c in candidates:
            csv_data.append({
                'Name': c['name'],
                'Email': c['email'],
                'Phone': c['phone'],
                'Overall Score': c['overall_score'],
                'Skills Score': c['skills_score'],
                'Experience Score': c['experience_score'],
                'Education Score': c['education_score'],
                'Total Experience': c['total_experience'],
                'Matched Skills': ', '.join(c['matched_skills'][:5]),
                'Missing Skills': ', '.join(c['missing_skills'][:5])
            })
        
        df = pd.DataFrame(csv_data)
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="📊 Download CSV",
            data=csv,
            file_name=f"ranking_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    
    def get_sample_job_description(self):
            """Return sample job description"""
            return """Senior Python Developer

    We are seeking an experienced Python Developer to join our AI/ML team.

    Requirements:
    - 3-5 years of professional Python development experience
    - Strong experience with Machine Learning frameworks (TensorFlow, PyTorch)
    - Experience with cloud platforms (AWS preferred)
    - Bachelor's degree in Computer Science or related field

    Must Have Skills:
    - Python (expert level)
    - Machine Learning & Deep Learning
    - TensorFlow or PyTorch
    - SQL databases (MySQL, PostgreSQL)
    - REST API development
    - Git version control

    Nice to Have:
    - AWS/Azure/GCP experience
    - Docker and Kubernetes
    - React or frontend experience
    - Experience with NLP projects
    - CI/CD pipelines

    Responsibilities:
    - Develop and deploy machine learning models
    - Build scalable ML pipelines
    - Collaborate with data scientists and engineers
    - Write clean, maintainable, well-documented code
    - Participate in code reviews
    """
    # Main application entry point
if __name__ == "__main__":
        app = ResumeShortlistingApp()
        app.run()