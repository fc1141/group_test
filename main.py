import streamlit as st
import pandas as pd
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# 페이지 설정
st.set_page_config(
    page_title="예상매출액 산정서 자동화 시스템",
    page_icon="📊",
    layout="wide"
)

# 세션 상태 초기화
if 'calculation_method' not in st.session_state:
    st.session_state.calculation_method = "A형: 인근 가맹점 매출 활용"
if 'competitor_data' not in st.session_state:
    st.session_state.competitor_data = pd.DataFrame({
        '업체명': ['', '', ''],
        '거리(m)': [0, 0, 0],
        '업종': ['', '', ''],
        '비고': ['', '', '']
    })
if 'nearby_stores' not in st.session_state:
    st.session_state.nearby_stores = pd.DataFrame({
        '점포명': ['점포1', '점포2', '점포3', '점포4', '점포5'],
        '월매출액(만원)': [0, 0, 0, 0, 0],
        '면적(㎡)': [0.0, 0.0, 0.0, 0.0, 0.0],
        '영업일수': [30, 30, 30, 30, 30]
    })

# 핵심 로직 함수들
def calculate_nearby_sales_result(sales_data, target_area):
    """인근 5개점 매출 환산액 계산"""
    try:
        # 매출 환산액 계산 (㎡당 일매출액)
        sales_data['매출환산액'] = (sales_data['월매출액(만원)'] / sales_data['영업일수']) / sales_data['면적(㎡)']
        
        # 유효한 데이터만 필터링
        valid_data = sales_data[sales_data['매출환산액'] > 0]['매출환산액'].tolist()
        
        if len(valid_data) >= 3:
            sorted_data = sorted(valid_data)
            # 최고, 최저 제외한 나머지 데이터
            if len(sorted_data) >= 5:
                target_data = sorted_data[1:4]  # 5개 중 최고/최저 제외
            else:
                target_data = sorted_data  # 3-4개인 경우 모두 사용
            
            min_val = min(target_data)
            max_val = max(target_data)
            
            # 예정 점포 면적 기준 월매출액 계산
            min_monthly = min_val * target_area * 30
            max_monthly = max_val * target_area * 30
            
            # 결과 표시
            st.success("✅ 매출 환산액 계산 완료")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("최저 예상매출액", f"{min_monthly:,.0f}만원/월")
            with col2:
                st.metric("최고 예상매출액", f"{max_monthly:,.0f}만원/월")
            with col3:
                ratio = max_monthly / min_monthly if min_monthly > 0 else 0
                st.metric("최고/최저 비율", f"{ratio:.2f}배")
            
            # 법적 기준 검증
            is_valid, message = check_legal_ratio(min_monthly, max_monthly)
            if is_valid:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ {message}")
            
            # 세션에 결과 저장
            st.session_state.calculation_result = {
                'min_sales': min_monthly,
                'max_sales': max_monthly,
                'method': 'A형',
                'valid': is_valid
            }
            
        else:
            st.error("❌ 최소 3개 이상의 유효한 매출 데이터가 필요합니다.")
            
    except Exception as e:
        st.error(f"❌ 계산 중 오류가 발생했습니다: {str(e)}")

def check_legal_ratio(min_sales, max_sales):
    """1.7배 법적 규정 검증"""
    if min_sales <= 0:
        return False, "최저 매출액이 0보다 커야 합니다."
    
    ratio = max_sales / min_sales
    if ratio > 1.7:
        return False, f"법적 기준(1.7배)을 초과했습니다. 현재 비율: {ratio:.2f}배"
    return True, f"법적 기준을 준수하고 있습니다. 현재 비율: {ratio:.2f}배"

def generate_pdf_report(data):
    """PDF 리포트 생성"""
    try:
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # 제목
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "Expected Sales Calculation Report")
        
        # 기본 정보
        p.setFont("Helvetica", 12)
        y_position = height - 100
        
        p.drawString(50, y_position, f"Creation Date: {data['creation_date']}")
        y_position -= 20
        p.drawString(50, y_position, f"Author: {data['author_name']}")
        y_position -= 40
        
        # 가맹본부 정보
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y_position, "Franchise Information")
        y_position -= 20
        
        p.setFont("Helvetica", 10)
        p.drawString(50, y_position, f"Brand: {data['franchise_brand']}")
        y_position -= 15
        p.drawString(50, y_position, f"CEO: {data['franchise_ceo']}")
        y_position -= 15
        p.drawString(50, y_position, f"Address: {data['franchise_address']}")
        y_position -= 30
        
        # 가맹희망자 정보
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y_position, "Applicant Information")
        y_position -= 20
        
        p.setFont("Helvetica", 10)
        p.drawString(50, y_position, f"Name: {data['applicant_name']}")
        y_position -= 15
        p.drawString(50, y_position, f"Store Address: {data['store_address']}")
        y_position -= 15
        p.drawString(50, y_position, f"Store Area: {data['store_area']} sqm")
        y_position -= 30
        
        # 계산 결과
        if 'calculation_result' in st.session_state:
            result = st.session_state.calculation_result
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, y_position, "Sales Calculation Result")
            y_position -= 20
            
            p.setFont("Helvetica", 10)
            p.drawString(50, y_position, f"Method: {data['calculation_method']}")
            y_position -= 15
            p.drawString(50, y_position, f"Minimum Expected Sales: {result['min_sales']:,.0f} KRW/month")
            y_position -= 15
            p.drawString(50, y_position, f"Maximum Expected Sales: {result['max_sales']:,.0f} KRW/month")
            y_position -= 15
            
            status = "Compliant" if result['valid'] else "Non-compliant"
            p.drawString(50, y_position, f"Legal Compliance (1.7x ratio): {status}")
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        st.error(f"PDF 생성 중 오류가 발생했습니다: {str(e)}")
        return None

def generate_markdown_report(data):
    """Markdown 리포트 생성"""
    content = f"""# 예상매출액 산정서

## 기본 정보
- **작성일자**: {data['creation_date']}
- **작성자**: {data['author_name']}

## 가맹본부 정보
- **영업표지**: {data['franchise_brand']}
- **대표자**: {data['franchise_ceo']}
- **주소**: {data['franchise_address']}

## 가맹희망자 정보
- **성명**: {data['applicant_name']}
- **점포 예정지**: {data['store_address']}
- **예정 면적**: {data['store_area']}㎡

## 매출 산출 결과
- **산출 방식**: {data['calculation_method']}
"""
    
    if 'calculation_result' in st.session_state:
        result = st.session_state.calculation_result
        content += f"""
- **최저 예상매출액**: {result['min_sales']:,.0f}만원/월
- **최고 예상매출액**: {result['max_sales']:,.0f}만원/월
- **법적 기준 준수**: {'✅ 준수' if result['valid'] else '❌ 미준수'}

## 상권 분석
### 점포 정보
- **보증금**: {data['deposit']:,}만원
- **월세**: {data['monthly_rent']:,}만원
- **기존 업종**: {data['previous_business']}

### 주변 환경
{data['major_facilities']}

---
*본 산정서는 가맹사업법 시행령에 따라 작성되었습니다.*
"""
    
    return content

# 메인 UI 시작
st.title("📊 예상매출액 산정서 자동화 시스템")
st.markdown("가맹본부 담당자를 위한 법적 기준 준수 매출 산정 도구")
st.markdown("---")

# 사이드바 설정
with st.sidebar:
    st.title("🏪 설정")
    st.markdown("---")
    
    # 로고 업로드
    uploaded_logo = st.file_uploader("로고 업로드", type=['png', 'jpg', 'jpeg'])
    
    # 산출 방식 선택
    calculation_method = st.selectbox(
        "산출 방식 선택",
        ["A형: 인근 가맹점 매출 활용", "B형: 가맹본부 예측 방식"]
    )
    st.session_state.calculation_method = calculation_method
    
    # 작성 정보
    st.markdown("### 작성 정보")
    creation_date = st.date_input("작성일자", datetime.now())
    author_name = st.text_input("작성자", "")

# 1. 기본 정보 섹션
st.header("📋 1. 기본 정보")
col1, col2 = st.columns(2)

with col1:
    st.subheader("가맹본부 정보")
    franchise_brand = st.text_input("영업표지(브랜드명)", "")
    franchise_ceo = st.text_input("대표자명", "")
    franchise_address = st.text_area("가맹본부 주소", "")

with col2:
    st.subheader("가맹희망자 정보")
    applicant_name = st.text_input("가맹희망자 성명", "")
    store_address = st.text_area("점포 예정지 주소", "")
    store_area = st.number_input("예정 면적(㎡)", min_value=0.0, step=0.1)

st.markdown("---")

# 2. 상권 분석 섹션
st.header("🏢 2. 상권 분석")
col1, col2 = st.columns(2)

with col1:
    st.subheader("점포 정보")
    deposit = st.number_input("보증금(만원)", min_value=0, step=100)
    monthly_rent = st.number_input("월세(만원)", min_value=0, step=10)
    previous_business = st.text_input("기존 업종", "")

with col2:
    st.subheader("상권 정보")
    major_facilities = st.text_area("주변 주요 시설", placeholder="오피스, 아파트, 학교 등")

st.subheader("경쟁점 현황")
competitor_data = st.data_editor(
    st.session_state.competitor_data,
    num_rows="dynamic",
    width="stretch"
)
st.session_state.competitor_data = competitor_data

st.markdown("---")

# 3. 매출 산출 섹션
st.header("💰 3. 매출 산출")

if st.session_state.calculation_method == "A형: 인근 가맹점 매출 활용":
    st.subheader("인근 5개 가맹점 매출 데이터")
    st.info("시행령 제9조 제4항에 따른 인근 가맹점 매출 활용 방식")
    
    nearby_stores = st.data_editor(
        st.session_state.nearby_stores,
        width="stretch"
    )
    st.session_state.nearby_stores = nearby_stores
    
    # 매출 환산액 계산 및 표시
    if st.button("💡 매출 환산액 계산", type="primary"):
        if store_area > 0:
            calculate_nearby_sales_result(nearby_stores, store_area)
        else:
            st.error("❌ 점포 면적을 먼저 입력해주세요.")

else:  # B형: 가맹본부 예측 방식
    st.subheader("가맹본부 예측 방식")
    st.info("시행령 제9조 제3항에 따른 가맹본부 예측 방식")
    
    col1, col2 = st.columns(2)
    with col1:
        predicted_min = st.number_input("예상 최저 매출액(만원/월)", min_value=0, step=100)
    with col2:
        predicted_max = st.number_input("예상 최고 매출액(만원/월)", min_value=0, step=100)
    
    prediction_basis = st.text_area("예측 근거", placeholder="유사 가맹점 평균 매출액, 유동인구 기반 산식 등")
    
    # B형 계산 버튼
    if st.button("💡 예측 매출액 검증", type="primary"):
        if predicted_min > 0 and predicted_max > 0:
            is_valid, message = check_legal_ratio(predicted_min, predicted_max)
            if is_valid:
                st.success(f"✅ {message}")
                # 세션에 결과 저장
                st.session_state.calculation_result = {
                    'min_sales': predicted_min,
                    'max_sales': predicted_max,
                    'method': 'B형',
                    'valid': is_valid,
                    'basis': prediction_basis
                }
            else:
                st.error(f"❌ {message}")
        else:
            st.error("❌ 최저 및 최고 매출액을 모두 입력해주세요.")

st.markdown("---")

# 4. 결과 확인 및 리포트 생성 섹션
st.header("📄 4. 결과 확인 및 리포트")

# 입력 데이터 검증
required_fields = [franchise_brand, franchise_ceo, applicant_name, store_address, store_area]

if all(field for field in required_fields) and store_area > 0:
    st.success("✅ 모든 필수 정보가 입력되었습니다.")
    
    # 미리보기
    st.subheader("📋 산정서 미리보기")
    
    with st.container():
        st.markdown("### 예상매출액 산정서")
        st.markdown(f"**작성일자:** {creation_date}")
        st.markdown(f"**작성자:** {author_name}")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**가맹본부 정보**")
            st.write(f"• 영업표지: {franchise_brand}")
            st.write(f"• 대표자: {franchise_ceo}")
            st.write(f"• 주소: {franchise_address}")
        
        with col2:
            st.markdown("**가맹희망자 정보**")
            st.write(f"• 성명: {applicant_name}")
            st.write(f"• 점포 예정지: {store_address}")
            st.write(f"• 예정 면적: {store_area}㎡")
        
        st.markdown("---")
        st.markdown(f"**산출 방식:** {st.session_state.calculation_method}")
        
        # 계산 결과 표시
        if 'calculation_result' in st.session_state:
            result = st.session_state.calculation_result
            st.markdown("**예상 매출액 범위**")
            st.write(f"• 최저 예상매출액: {result['min_sales']:,.0f}만원/월")
            st.write(f"• 최고 예상매출액: {result['max_sales']:,.0f}만원/월")
            
            if result['valid']:
                st.success("✅ 법적 기준(최고/최저 1.7배 이하) 준수")
            else:
                st.error("❌ 법적 기준 미준수 - 범위 조정 필요")
    
    # 리포트 생성 버튼
    st.subheader("📥 리포트 다운로드")
    col1, col2 = st.columns(2)
    
    # 데이터 수집
    report_data = {
        'creation_date': creation_date,
        'author_name': author_name,
        'franchise_brand': franchise_brand,
        'franchise_ceo': franchise_ceo,
        'franchise_address': franchise_address,
        'applicant_name': applicant_name,
        'store_address': store_address,
        'store_area': store_area,
        'calculation_method': st.session_state.calculation_method,
        'deposit': deposit,
        'monthly_rent': monthly_rent,
        'previous_business': previous_business,
        'major_facilities': major_facilities
    }
    
    with col1:
        if st.button("📄 PDF 리포트 생성", type="primary"):
            pdf_buffer = generate_pdf_report(report_data)
            if pdf_buffer:
                st.download_button(
                    label="📥 PDF 다운로드",
                    data=pdf_buffer,
                    file_name=f"예상매출액산정서_{applicant_name}_{creation_date}.pdf",
                    mime="application/pdf"
                )
    
    with col2:
        if st.button("📝 Markdown 리포트 생성"):
            markdown_content = generate_markdown_report(report_data)
            st.download_button(
                label="📥 Markdown 다운로드",
                data=markdown_content,
                file_name=f"예상매출액산정서_{applicant_name}_{creation_date}.md",
                mime="text/markdown"
            )

else:
    st.warning("⚠️ 필수 정보를 모두 입력해주세요.")
    missing_fields = []
    if not franchise_brand: missing_fields.append("브랜드명")
    if not franchise_ceo: missing_fields.append("대표자명")
    if not applicant_name: missing_fields.append("가맹희망자 성명")
    if not store_address: missing_fields.append("점포 예정지 주소")
    if store_area <= 0: missing_fields.append("점포 면적")
    
    st.write(f"누락된 항목: {', '.join(missing_fields)}")

# 푸터
st.markdown("---")
st.markdown("💡 **도움말**: 위에서부터 순서대로 정보를 입력하시면 법적 기준에 맞는 예상매출액 산정서를 자동으로 생성할 수 있습니다.")
st.markdown("📞 **문의**: 시스템 관련 문의사항이 있으시면 담당자에게 연락해주세요.")