#!/usr/bin/env python3
"""Generate authoritative Vietnamese Crop Cultivation & Care Guides (vn_crop_guides.json).

All 15 crop groups match vn_diseases.json and link each phenological stage
to canonical CABI PlantwisePlus Vietnam disease entries stored locally on the server.
"""
import json
import os

GUIDES = [
    {
        "crop": "Chè",
        "scientific_name": "Camellia sinensis",
        "source_agency": "Viện KHKT Nông lâm nghiệp miền núi phía Bắc (NOMAFSI) & Trung tâm Khuyến nông Quốc gia",
        "summary_vi": "Cây công nghiệp dài ngày ưa khí hậu mát ẩm (18–25°C), đất đỏ vàng tơi xốp thoát nước tốt, tầng canh tác dày >60cm và độ chua pH KCl từ 4.5–5.5.",
        "summary_en": "Perennial industrial crop thriving in cool humid climates (18–25°C), well-drained ferralsols with >60cm soil depth and acidic pH (4.5–5.5).",
        "stages": [
            {
                "stage_number": 1,
                "title_vi": "Giai đoạn 1: Chuẩn bị đất, giống & Trồng mới",
                "title_en": "Stage 1: Land Preparation, Nursery & Planting",
                "timing_vi": "Tháng 1–3 (vụ Xuân) hoặc Tháng 8–10 (vụ Thu)",
                "timing_en": "Jan–Mar (Spring) or Aug–Oct (Autumn)",
                "care_vi": "Cày sâu 35–40cm, đào rãnh rộng 40cm sâu 35cm theo đường đồng mức. Bón lót 20–30 tấn phân chuồng hoai mục + 500kg lân nung chảy/ha. Chọn bầu chè giâm cành 8–10 tháng tuổi (LDP1, LDP2, Kim Tuyên, Shan) khỏe mạnh, trồng hàng kép mật độ 14.000–16.000 cây/ha, tủ gốc giữ ẩm bằng cỏ khô dày 8–10cm.",
                "care_en": "Subsoil 35–40cm along contour lines. Apply 20–30 tons composted manure + 500kg fused phosphate/ha as basal fertilizer. Plant 8–10 month-old disease-free cuttings at 14,000–16,000 plants/ha and mulch heavily.",
                "notes_vi": "Tuyệt đối không trồng chè trên đất ngập úng hoặc pH > 6.0. Không để bầu chè tiếp xúc trực tiếp với phân hóa học khi lấp đất.",
                "notes_en": "Avoid waterlogged soils or pH > 6.0. Never let bare roots touch chemical fertilizer directly.",
                "common_diseases": [
                    "Bệnh chấm xám lá chè"
                ]
            },
            {
                "stage_number": 2,
                "title_vi": "Giai đoạn 2: Kiến thiết cơ bản & Đốn tạo hình (1–3 tuổi)",
                "title_en": "Stage 2: Juvenile Establishment & Formative Pruning (Years 1–3)",
                "timing_vi": "Năm thứ 1 đến năm thứ 3 sau trồng",
                "timing_en": "Years 1 to 3 after planting",
                "care_vi": "Thực hiện đốn tạo hình 3 lần vào tháng 12–1 hàng năm: Năm 1 đốn thân chính cao 20–25cm; Năm 2 đốn cành cấp 1 cao 35–40cm; Năm 3 đốn cao 50–55cm tạo bộ khung tán phẳng vững chắc. Bón thúc NPK (tỷ lệ 2:1:1) chia 4 lần/năm kết hợp trồng cây phân xanh (cốt khí, muồng lá nhọn) xen giữa hàng chè.",
                "care_en": "Perform 3 annual formative prunings in Dec–Jan (20–25cm Year 1; 35–40cm Year 2; 50–55cm Year 3) to build a wide plucking table. Apply NPK (2:1:1) in 4 split doses/year with intercropped green manure.",
                "notes_vi": "Sau khi đốn phải quét vôi hoặc phun dung dịch Booc-đô 1% để sát trùng vết cắt và dọn sạch cành tăm, cành sâu bệnh.",
                "notes_en": "Sanitize pruning cuts with 1% Bordeaux mixture and remove weak/diseased twigs.",
                "common_diseases": [
                    "Bệnh chấm xám lá chè",
                    "Rầy xanh hại chè",
                    "Bọ xít muỗi hại chè"
                ]
            },
            {
                "stage_number": 3,
                "title_vi": "Giai đoạn 3: Phát triển búp lứa Xuân – Hè (Bật mầm & Phân cành)",
                "title_en": "Stage 3: Spring–Summer Flush & Shoot Elongation",
                "timing_vi": "Tháng 2 – Tháng 6 hàng năm",
                "timing_en": "February – June annually",
                "care_vi": "Chè bật mầm mạnh sau kỳ ngủ đông. Bón thúc mạnh phân đạm + kali + vi lượng (Zn, Mg, B) sau mỗi lứa hái hoặc đầu các đợt mưa xuân. Duy trì độ ẩm đất 70–80% bằng tưới phun mưa tiết kiệm.",
                "care_en": "Vigorous shoot flushing after winter dormancy. Top-dress N-K and micronutrients (Zn, Mg, B) after plucking rounds; maintain 70–80% soil moisture via sprinkler irrigation.",
                "notes_vi": "Thời tiết mưa phùn ẩm độ >85% đầu xuân và giao mùa rất thuận lợi cho nấm phồng lá và bọ xít muỗi bùng phát gây mù búp.",
                "notes_en": "High spring humidity (>85%) and drizzle trigger blister blight and mosquito bug outbreaks.",
                "common_diseases": [
                    "Bệnh phồng lá chè",
                    "Bọ xít muỗi hại chè",
                    "Rầy xanh hại chè"
                ]
            },
            {
                "stage_number": 4,
                "title_vi": "Giai đoạn 4: Kinh doanh búp chính vụ Hè – Thu & Hái tạo tán",
                "title_en": "Stage 4: Peak Summer–Autumn Plucking & Canopy Maintenance",
                "timing_vi": "Tháng 6 – Tháng 10 hàng năm",
                "timing_en": "June – October annually",
                "care_vi": "Thu hái theo nguyên tắc '1 tôm 2–3 lá non', chừa lại 1–2 lá thật trên cành (hái chừa xanh) để giữ diện tích quang hợp. Chu kỳ hái 7–12 ngày/lứa tùy giống. Bón bổ sung NPK sau mỗi 2 lứa hái và tưới phun mưa vào chiều mát để rửa trôi nhện đỏ trong các đợt nắng hạn.",
                "care_en": "Pluck '1 bud + 2–3 young leaves' every 7–12 days while leaving 1–2 maintenance leaves. Apply NPK every 2 plucking rounds and overhead-mist in late afternoon during dry spells.",
                "notes_vi": "Tuyệt đối tuân thủ thời gian cách ly thuốc BVTV trước khi thu hái búp; ưu tiên chế phẩm sinh học (Matrine, Abamectin, Beauveria).",
                "notes_en": "Strictly observe Pre-Harvest Intervals (PHI) before plucking; prioritize bio-pesticides.",
                "common_diseases": [
                    "Bệnh thối búp chè (Thán thư chè)",
                    "Rầy xanh hại chè",
                    "Nhện đỏ nâu hại chè",
                    "Bọ xít muỗi hại chè"
                ]
            },
            {
                "stage_number": 5,
                "title_vi": "Giai đoạn 5: Đốn phớt cuối vụ, Vệ sinh nương chè & Ngủ đông",
                "title_en": "Stage 5: Winter Skiffing/Pruning, Field Sanitation & Dormancy",
                "timing_vi": "Tháng 11 – Tháng 1 năm sau",
                "timing_en": "November – January",
                "care_vi": "Ngừng hái búp từ cuối tháng 11, tiến hành đốn phớt (cao hơn vết đốn năm trước 3–5cm) hoặc đốn lửng (sau 3–4 năm). Cày xới nhẹ giữa hàng sâu 15–20cm để vùi phân hữu cơ vi sinh + phân lân cho vụ sau.",
                "care_en": "Cease plucking in late November; perform winter skiffing (+3–5cm above last year's cut). Cultivate inter-rows 15–20cm deep to incorporate bio-organic manure and phosphorus.",
                "notes_vi": "Thu gom lá rụng, cành bệnh đem tiêu hủy và phun lưu huỳnh vôi (Lime sulfur) hoặc dầu khoáng để diệt nguồn trứng nhện đỏ, bào tử nấm qua đông.",
                "notes_en": "Clear fallen leaves/diseased branches and spray lime sulfur or mineral oil to eradicate overwintering mite eggs and fungal spores.",
                "common_diseases": [
                    "Nhện đỏ nâu hại chè",
                    "Bệnh chấm xám lá chè",
                    "Bệnh thối búp chè (Thán thư chè)"
                ]
            }
        ]
    },
    {
        "crop": "Cam/Bưởi",
        "scientific_name": "Citrus sinensis / Citrus maxima",
        "source_agency": "Viện Cây ăn quả miền Nam (SOFRI) & Viện Nghiên cứu Rau quả (FAVRI)",
        "summary_vi": "Nhóm cây ăn quả có múi giá trị cao, yêu cầu đất thịt nhẹ hoặc phù sa thoát nước tốt, pH 5.5–6.5, mực nước ngầm sâu >1m và cây giống sạch bệnh trồng từ nhà lưới.",
        "summary_en": "High-value citrus crops requiring well-drained loamy/alluvial soil, pH 5.5–6.5, water table >1m deep, and certified disease-free screenhouse saplings.",
        "stages": [
            {
                "stage_number": 1,
                "title_vi": "Giai đoạn 1: Thiết kế vườn, Đắp mô & Trồng cây giống sạch bệnh",
                "title_en": "Stage 1: Orchard Design, Mound Building & Certified Planting",
                "timing_vi": "Đầu mùa mưa (Tháng 4–6) hoặc vụ Xuân (Tháng 2–3)",
                "timing_en": "Early rainy season (Apr–Jun) or Spring (Feb–Mar)",
                "care_vi": "Đào mương lên liếp, đắp mô cao 40–60cm (vùng thấp) hoặc đào hố 60x60x60cm. Bón lót 20–30kg phân hữu cơ hoai mục ủ nấm đối kháng Trichoderma + 0.5kg lân + 0.5kg vôi bột/hố trước trồng 30 ngày. Chọn cây ghép khỏe mạnh, sạch bệnh Greening (HLB) và Tristeza.",
                "care_en": "Build raised beds and mounds 40–60cm high; mix 20–30kg Trichoderma-enriched compost + 0.5kg P + 0.5kg lime per pit 30 days prior. Plant certified HLB-free grafted saplings.",
                "notes_vi": "Không trồng quá sâu làm lấp mắt ghép (mắt ghép phải cao hơn mặt mô 10–15cm) để tránh nấm Phytophthora xâm nhiễm cổ rễ.",
                "notes_en": "Keep the graft union 10–15cm above soil level to prevent Phytophthora collar rot.",
                "common_diseases": [
                    "Bệnh vàng lá thối rễ và xì mủ gốc cây có múi",
                    "Bệnh vàng lá gân xanh (Greening / HLB)"
                ]
            },
            {
                "stage_number": 2,
                "title_vi": "Giai đoạn 2: Kiến thiết cơ bản & Điều khiển các đợt cơi đọt",
                "title_en": "Stage 2: Canopy Architecture & Synchronized Flush Management",
                "timing_vi": "Năm 1–2 & Các đợt ra lộc non trong năm",
                "timing_en": "Years 1–2 & Annual vegetative flushes",
                "care_vi": "Tỉa cành tạo tán theo nguyên tắc '1 thân chính – 3 cành cấp 1 – 9 cành cấp 2' phân bố đều các hướng. Bón phân giàu Đạm - Lân (NPK 20-20-15 hoặc 30-10-10) trước khi cây nhú đọt 7–10 ngày để các cơi đọt ra đồng loạt.",
                "care_en": "Train canopy to '1 trunk – 3 primary – 9 secondary branches'. Apply high N-P fertilizer 7–10 days before budbreak so young flushes emerge uniformly.",
                "notes_vi": "Giai đoạn cơi đọt non dài 0.5–5cm là thời điểm nhạy cảm nhất với Sâu vẽ bùa, Rầy chổng cánh (môi giới bệnh HLB) và vi khuẩn Loét cam.",
                "notes_en": "Young flushes (0.5–5cm) are critically vulnerable to citrus leafminer, Asian citrus psyllid (HLB vector), and bacterial canker.",
                "common_diseases": [
                    "Sâu vẽ bùa hại cây có múi",
                    "Rầy mềm hại cây có múi",
                    "Bệnh loét cây có múi (Loét cam)",
                    "Bệnh vàng lá gân xanh (Greening / HLB)"
                ]
            },
            {
                "stage_number": 3,
                "title_vi": "Giai đoạn 3: Xử lý phân hóa mầm hoa, Ra hoa & Đậu quả non",
                "title_en": "Stage 3: Flower Induction, Blooming & Fruit Set",
                "timing_vi": "Tháng 12 – Tháng 3 (chính vụ) hoặc xử lý rải vụ",
                "timing_en": "December – March (main season) or staggered induction",
                "care_vi": "Bón phân giàu Lân và Kali (MKP, K2SO4), xiết nước vừa phải 15–25 ngày khi bộ lá cơi cuối đã thuần thục, sau đó tưới đẫm trở lại để kích thích ra hoa tập trung. Bổ sung Bo và Canxi qua lá trước khi hoa nở và sau khi rụng cánh hoa 80% để tăng tỷ lệ đậu quả.",
                "care_en": "Apply high P-K fertilizer, impose mild water stress for 15–25 days once leaves mature, then re-water deeply to trigger uniform bloom. Spray Boron and Calcium pre-bloom and at 80% petal fall.",
                "notes_vi": "Tránh phun thuốc BVTV dạng nhũ dầu (EC) nóng khi hoa đang nở rộ; theo dõi sát nấm ghẻ nhám và nhện tấn công bầu nhụy non.",
                "notes_en": "Avoid spraying hot EC formulations during full bloom; monitor closely for citrus scab and mites on young fruitlets.",
                "common_diseases": [
                    "Bệnh ghẻ nhám cây có múi (Ghẻ lồi)",
                    "Rầy mềm hại cây có múi",
                    "Nhện đỏ và Nhện rám vàng hại cây có múi"
                ]
            },
            {
                "stage_number": 4,
                "title_vi": "Giai đoạn 4: Nuôi quả lớn & Bảo vệ vỏ quả thương phẩm",
                "title_en": "Stage 4: Fruit Development & Rind Quality Protection",
                "timing_vi": "Từ 1 đến 6 tháng sau đậu quả",
                "timing_en": "1 to 6 months after fruit set",
                "care_vi": "Tỉa bỏ quả dị dạng, quả sâu bệnh và quả mọc chùm quá dày. Bón NPK cân đối (16-16-16) giai đoạn quả nhỏ và tăng hàm lượng Kali (12-12-17+TE) ở 2 tháng cuối. Tưới đủ ẩm đều đặn để tránh nứt quả, kết hợp bao trái bưởi khi quả bằng nắm tay.",
                "care_en": "Thin deformed/clustered fruits. Apply balanced NPK (16-16-16) during early expansion and high-K (12-12-17+TE) in the last 2 months. Maintain steady moisture to prevent fruit splitting and bag pummelo fruits.",
                "notes_vi": "Nhện rám vàng rất nhỏ (mắt thường không thấy), nếu không kiểm soát ở giai đoạn quả bằng quả bóng bàn sẽ làm vỏ cam/bưởi bị da lu, da cám đen sạm.",
                "notes_en": "Citrus rust mites are microscopic; unchecked infestations at golf-ball stage cause bronzed/russeted rind ('da lu, da cám').",
                "common_diseases": [
                    "Nhện đỏ và Nhện rám vàng hại cây có múi",
                    "Bệnh loét cây có múi (Loét cam)",
                    "Bệnh ghẻ nhám cây có múi (Ghẻ lồi)"
                ]
            },
            {
                "stage_number": 5,
                "title_vi": "Giai đoạn 5: Thu hoạch, Tỉa cành phục hồi & Phòng thối rễ mùa mưa",
                "title_en": "Stage 5: Harvest, Post-Harvest Pruning & Root Rot Prevention",
                "timing_vi": "Thu hoạch & Sau thu hoạch 15–30 ngày",
                "timing_en": "Harvest & 15–30 days post-harvest",
                "care_vi": "Thu hoạch khi quả đạt độ chín sinh lý vào ngày nắng ráo, cắt cuống sát quả không làm dập túi tinh dầu. Sau thu hoạch 7–15 ngày, cắt tỉa cành vượt, cành khô, cành mang cuống quả; bón vôi nâng pH đất + phân hữu cơ vi sinh Trichoderma quanh hình chiếu tán.",
                "care_en": "Harvest on dry days by clipping stems flush with the fruit button. Within 7–15 days post-harvest, prune dead/fruiting twigs and apply agricultural lime + Trichoderma organic manure around the drip line.",
                "notes_vi": "Kiểm tra cổ rễ định kỳ đầu và cuối mùa mưa; nếu thấy vết xì mủ phải cạo sạch phần vỏ thối và quét thuốc gốc Đồng hoặc Fosetyl-Aluminium ngay.",
                "notes_en": "Inspect root collars before and after the rainy season; scrape gummosis lesions clean and paint with copper or Fosetyl-Al immediately.",
                "common_diseases": [
                    "Bệnh vàng lá thối rễ và xì mủ gốc cây có múi",
                    "Bệnh vàng lá gân xanh (Greening / HLB)"
                ]
            }
        ]
    },
    {
        "crop": "Lúa",
        "scientific_name": "Oryza sativa",
        "source_agency": "Cục Trồng trọt, Viện Lúa ĐBSCL (CLRRI) & Trung tâm Khuyến nông Quốc gia",
        "summary_vi": "Cây lương thực chủ lực áp dụng quy trình canh tác tiên tiến '1 Phải 5 Giảm' và '3 Giảm 3 Tăng', tưới nước ngập – khô xen kẽ (AWD) giúp bộ rễ khỏe, cứng cây, chống đổ ngã.",
        "summary_en": "Staple food crop managed under Vietnam's '1 Must Do, 5 Reductions' (1M5R) and Alternate Wetting and Drying (AWD) irrigation for strong roots and lodging resistance.",
        "stages": [
            {
                "stage_number": 1,
                "title_vi": "Giai đoạn 1: Làm đất, Vệ sinh đồng ruộng, Xử lý giống & Gieo sạ",
                "title_en": "Stage 1: Land Preparation, Seed Treatment & Sowing",
                "timing_vi": "Trước sạ 15 ngày đến 0–7 ngày sau sạ (NSS)",
                "timing_en": "15 days pre-sowing to 0–7 days after sowing (DAS)",
                "care_vi": "Cày vùi rơm rạ kết hợp phun chế phẩm nấm Trichoderma phân hủy hữu cơ ít nhất 2–3 tuần trước sạ; trang phẳng mặt ruộng và đánh rãnh thoát nước phèn. Sử dụng giống lúa xác nhận ('1 Phải'), lượng giống giảm còn 80–100 kg/ha (sạ hàng/sạ cụm) hoặc 40–60 kg/ha (cấy máy).",
                "care_en": "Incorporate straw with Trichoderma 2–3 weeks before sowing; laser-level fields and dig drainage trenches. Use certified seed ('1 Must') at reduced rates: 80–100 kg/ha (row seeding) or 40–60 kg/ha (transplanting).",
                "notes_vi": "Nếu cày vùi rơm rạ tươi rồi gieo sạ ngay trong điều kiện ngập nước yếm khí sẽ gây ngộ độc hữu cơ (nghẹt rễ) làm cây lúa lụi dần.",
                "notes_en": "Flooding fresh straw immediately before sowing causes anaerobic organic acid toxicity (root suffocation).",
                "common_diseases": [
                    "Bệnh nghẹt rễ sinh lý lúa (Ngộ độc hữu cơ / phèn)",
                    "Bệnh đốm nâu hại lúa (Tiêm lửa)"
                ]
            },
            {
                "stage_number": 2,
                "title_vi": "Giai đoạn 2: Mạ – Đẻ nhánh (7–35 ngày sau sạ)",
                "title_en": "Stage 2: Seedling to Active Tillering (7–35 DAS)",
                "timing_vi": "7 – 35 ngày sau sạ (NSS)",
                "timing_en": "7 – 35 days after sowing (DAS)",
                "care_vi": "Giữ mực nước nông 1–3cm để lúa đẻ nhánh thuận lợi. Bón thúc đợt 1 (7–10 NSS) và đợt 2 (18–22 NSS) theo bảng so màu lá lúa (LCC), kết hợp tỉa dặm sớm để mật độ đồng đều.",
                "care_en": "Keep shallow water (1–3cm) to promote tillering. Apply 1st top-dressing (7–10 DAS) and 2nd top-dressing (18–22 DAS) guided by the Leaf Color Chart (LCC).",
                "notes_vi": "Tuyệt đối KHÔNG phun thuốc trừ sâu ăn lá trong 40 ngày đầu sau sạ (vì cây lúa có khả năng tự đền bù lá rất mạnh và cần bảo tồn thiên địch bắt rầy nâu).",
                "notes_en": "NEVER spray insecticides against leaf-feeders in the first 40 DAS (rice compensates naturally and natural enemies of brown planthopper must be preserved).",
                "common_diseases": [
                    "Bệnh đạo ôn lúa (Đạo ôn lá & cổ bông)",
                    "Bệnh nghẹt rễ sinh lý lúa (Ngộ độc hữu cơ / phèn)",
                    "Sâu cuốn lá nhỏ hại lúa",
                    "Rầy nâu và Rầy lưng trắng hại lúa"
                ]
            },
            {
                "stage_number": 3,
                "title_vi": "Giai đoạn 3: Cuối đẻ nhánh – Làm đòng (Đứng cái – Phân hóa đòng)",
                "title_en": "Stage 3: Maximum Tillering to Panicle Initiation (35–55 DAS)",
                "timing_vi": "35 – 55 ngày sau sạ (NSS)",
                "timing_en": "35 – 55 days after sowing (DAS)",
                "care_vi": "Cuối giai đoạn đẻ nhánh (30–35 NSS) rút nước phơi ruộng 5–7 ngày đến khi mặt ruộng nứt chân chim để hạn chế chồi vô hiệu và giúp rễ ăn sâu. Khi bóc thân chính thấy đòng trắng (cứt gián 1–2mm) ở 40–45 NSS, cho nước vào và bón phân đón đòng (Đạm + Kali).",
                "care_en": "Drain fields at 30–35 DAS for 5–7 days until hairline soil cracks appear to suppress unproductive tillers. Re-flood and apply panicle initiation N-K fertilizer when the young panicle reaches 1–2mm (40–45 DAS).",
                "notes_vi": "Kiểm tra kỹ vết bệnh đạo ôn lá và khô vằn ở bẹ lá dưới gốc trước khi quyết định lượng đạm bón đón đòng; ruộng đang bị đạo ôn phải ngưng bón đạm.",
                "notes_en": "Inspect lower sheaths for blast and sheath blight before applying panicle N; withhold N if leaf blast is active.",
                "common_diseases": [
                    "Bệnh đạo ôn lúa (Đạo ôn lá & cổ bông)",
                    "Bệnh khô vằn hại lúa",
                    "Sâu cuốn lá nhỏ hại lúa",
                    "Bệnh bạc lá lúa (Cháy bìa lá)"
                ]
            },
            {
                "stage_number": 4,
                "title_vi": "Giai đoạn 4: Làm đòng già – Trỗ bông – Phơi màu",
                "title_en": "Stage 4: Booting, Heading & Flowering (55–75 DAS)",
                "timing_vi": "55 – 75 ngày sau sạ (NSS)",
                "timing_en": "55 – 75 days after sowing (DAS)",
                "care_vi": "Duy trì mực nước 3–5cm suốt giai đoạn lúa làm đòng đến trỗ đều (lúa rất mẫn cảm với hạn ở giai đoạn này). Bảo vệ tuyệt đối bộ 3 lá đòng (lá công năng quyết định 70% năng suất hạt).",
                "care_en": "Maintain 3–5cm water depth from booting through full heading. Protect the top 3 flag leaves which contribute >70% of grain filling.",
                "notes_vi": "Phun phòng đạo ôn cổ bông ở 2 thời điểm vàng: khi lúa trỗ lẹt xẹt (5%) và khi lúa trỗ đều (85–90%). Vạch gốc lúa kiểm tra mật độ rầy nâu lứa chính.",
                "notes_en": "Apply preventive neck-blast protection at two critical windows: 5% heading and full heading (85–90%). Part rice hills to monitor brown planthopper nymphs at the base.",
                "common_diseases": [
                    "Bệnh đạo ôn lúa (Đạo ôn lá & cổ bông)",
                    "Bệnh bạc lá lúa (Cháy bìa lá)",
                    "Bệnh khô vằn hại lúa",
                    "Rầy nâu và Rầy lưng trắng hại lúa"
                ]
            },
            {
                "stage_number": 5,
                "title_vi": "Giai đoạn 5: Vô gạo (Chín sữa, Chín sáp) & Thu hoạch",
                "title_en": "Stage 5: Grain Filling (Milk, Dough) & Harvest (75–100+ DAS)",
                "timing_vi": "75 ngày sau sạ đến Thu hoạch",
                "timing_en": "75 DAS to Harvest",
                "care_vi": "Bổ sung Kali hoặc chế phẩm sinh học giàu K-Si giúp hạt lúa vào chắc tới cậy, vỏ trấu vàng sáng. Rút cạn nước ruộng trước thu hoạch 7–10 ngày (khi bông lúa cong câu, 85–90% hạt trên bông đã chín vàng) để mặt ruộng khô ráo cho máy gặt đập liên hợp.",
                "care_en": "Maintain foliar K-Si nutrition for full grain filling. Drain the field completely 7–10 days before harvest (when 85–90% of spikelets turn golden) for combine harvesting.",
                "notes_vi": "Không bón bất kỳ loại phân đạm nào ở giai đoạn này; kiểm tra rầy nâu tuổi 2–3 dưới gốc để tránh hiện tượng 'cháy rầy' sát ngày gặt.",
                "notes_en": "Never apply nitrogen during grain filling; monitor late-season planthoppers to prevent 'hopperburn' right before harvest.",
                "common_diseases": [
                    "Rầy nâu và Rầy lưng trắng hại lúa",
                    "Bệnh đốm nâu hại lúa (Tiêm lửa)",
                    "Bệnh khô vằn hại lúa"
                ]
            }
        ]
    },
    {
        "crop": "Ngô",
        "scientific_name": "Zea mays",
        "source_agency": "Viện Nghiên cứu Ngô (MRI) & Cục Bảo vệ thực vật",
        "summary_vi": "Cây lương thực – thức ăn chăn nuôi ưa sáng, cần đất tơi xốp giàu dinh dưỡng (pH 5.5–7.0), quản lý nghiêm ngặt Sâu keo mùa thu ở giai đoạn cây con và tưới đủ ẩm khi xoáy nõn – trỗ cờ.",
        "summary_en": "C4 cereal crop requiring fertile, well-drained soil (pH 5.5–7.0), early-stage Fall Armyworm IPM, and adequate moisture during whorl-to-tasseling stages.",
        "stages": [
            {
                "stage_number": 1,
                "title_vi": "Giai đoạn 1: Làm đất, Bón lót & Gieo hạt (0–10 ngày sau gieo)",
                "title_en": "Stage 1: Tillage, Basal Fertilization & Sowing (0–10 DAS)",
                "timing_vi": "0 – 10 ngày sau gieo",
                "timing_en": "0 – 10 days after sowing",
                "care_vi": "Cày bừa kỹ, lên luống thoát nước tốt. Bón lót toàn bộ phân chuồng hoai mục (8–10 tấn/ha) + 100% phân lân + 20% đạm vào rãnh cách hạt 5–7cm. Chọn giống ngô lai năng suất cao (NK7328, CP511, LVN10, HN88) đã xử lý thuốc hạt, gieo khoảng cách 65–70cm x 25–28cm (mật độ 5.5–6.5 vạn cây/ha).",
                "care_en": "Prepare raised beds; apply 8–10 tons manure + 100% P + 20% N in furrows 5–7cm from seeds. Sow treated hybrid seeds at 65–70cm x 25–28cm spacing (55,000–65,000 plants/ha).",
                "notes_vi": "Gieo đồng loạt trên diện rộng để tránh sâu keo mùa thu chuyển lứa gây hại liên tục.",
                "notes_en": "Practice synchronized sowing across neighboring fields to break Fall Armyworm generational overlap.",
                "common_diseases": [
                    "Sâu keo mùa thu hại ngô"
                ]
            },
            {
                "stage_number": 2,
                "title_vi": "Giai đoạn 2: Cây con 3–7 lá (10–28 ngày sau gieo)",
                "title_en": "Stage 2: Seedling V3–V7 Stage (10–28 DAS)",
                "timing_vi": "10 – 28 ngày sau gieo",
                "timing_en": "10 – 28 days after sowing",
                "care_vi": "Dặm tỉa định cây lúc 3–4 lá thật. Khi ngô đạt 5–7 lá, tiến hành bón thúc lần 1 (30–40% Đạm + 30% Kali) kết hợp xới cỏ và vun gốc nhẹ lần 1 giúp bộ rễ chân kiềng sớm phát triển.",
                "care_en": "Thin seedlings at V3–V4. At V5–V7, apply 1st top-dressing (30–40% N + 30% K) combined with weeding and light hilling.",
                "notes_vi": "Đây là giai đoạn Sâu keo mùa thu đẻ trứng mạnh nhất; cần ngắt ổ trứng và phun chế phẩm sinh học (Bt, NPV, Emamectin) trực tiếp vào loa kèn khi sâu mới nở tuổi 1–2.",
                "notes_en": "Peak egg-laying window for Fall Armyworm; crush egg masses and direct bio-insecticide sprays (Bt, NPV, Emamectin) straight into the whorl against 1st–2nd instar larvae.",
                "common_diseases": [
                    "Sâu keo mùa thu hại ngô",
                    "Bệnh cháy lá lớn hại ngô (Đốm lá lớn)"
                ]
            },
            {
                "stage_number": 3,
                "title_vi": "Giai đoạn 3: Xoáy nõn (Loa kèn) – Vươn lóng mạnh (8–12 lá)",
                "title_en": "Stage 3: Deep Whorl & Rapid Stem Elongation (V8–V12)",
                "timing_vi": "28 – 48 ngày sau gieo",
                "timing_en": "28 – 48 days after sowing",
                "care_vi": "Khi ngô xoáy nõn (9–11 lá), bón thúc lần 2 (50% Đạm + 50% Kali) và vun gốc cao 15–20cm để lấp kín các đốt rễ chân kiềng, giúp cây chống đổ ngã trước gió bão.",
                "care_en": "At deep whorl stage (V9–V11), apply 2nd top-dressing (50% N + 50% K) and hill soil 15–20cm high around brace-root nodes to prevent lodging.",
                "notes_vi": "Kiểm tra các lá tầng dưới và trung tâm để phát hiện sớm vết bệnh cháy lá lớn hình thoi và ổ gỉ sắt mặt lá.",
                "notes_en": "Inspect lower and middle leaves early for cigar-shaped northern leaf blight lesions and rust pustules.",
                "common_diseases": [
                    "Sâu keo mùa thu hại ngô",
                    "Bệnh cháy lá lớn hại ngô (Đốm lá lớn)",
                    "Bệnh rỉ sắt hại ngô"
                ]
            },
            {
                "stage_number": 4,
                "title_vi": "Giai đoạn 4: Trỗ cờ – Phun râu – Thụ phấn",
                "title_en": "Stage 4: Tasseling, Silking & Pollination (VT–R1)",
                "timing_vi": "48 – 70 ngày sau gieo",
                "timing_en": "48 – 70 days after sowing",
                "care_vi": "Giai đoạn quyết định số hạt/bắp. Đảm bảo độ ẩm đất đạt 75–80% (nếu khô hạn lúc phun râu sẽ làm bắp bị đuôi chuột hoặc không kết hạt). Bón hết lượng Kali còn lại trước trỗ cờ 5–7 ngày.",
                "care_en": "Critical kernel-set stage. Maintain 75–80% soil moisture (drought during silking causes barren tips) and apply the remaining K fertilizer 5–7 days before tasseling.",
                "notes_vi": "Bảo vệ các lá phía trên bắp và lá bi; nếu sâu keo mùa thu cắn đứt râu ngô hoặc đục vào đỉnh bắp cần xử lý ngay.",
                "notes_en": "Protect ear leaves and silks; control Fall Armyworm larvae attacking tassels or boring into ear tips.",
                "common_diseases": [
                    "Bệnh rỉ sắt hại ngô",
                    "Bệnh cháy lá lớn hại ngô (Đốm lá lớn)",
                    "Sâu keo mùa thu hại ngô"
                ]
            },
            {
                "stage_number": 5,
                "title_vi": "Giai đoạn 5: Chín sữa – Chín sáp – Thu hoạch",
                "title_en": "Stage 5: Milk/Dough Stage, Physiological Maturity & Harvest",
                "timing_vi": "70 – 110 ngày sau gieo",
                "timing_en": "70 – 110 days after sowing",
                "care_vi": "Duy trì bộ lá xanh quang hợp nuôi hạt; có thể tỉa bỏ 2–3 lá già đã khô hoàn toàn sát gốc để ruộng thông thoáng. Thu hoạch ngô hạt khi lá bi khô vàng >80% và chân hạt xuất hiện 'vết sẹo đen' (chín sinh lý).",
                "care_en": "Keep upper foliage green for kernel filling; strip dead basal leaves to improve airflow. Harvest grain corn when >80% of husks dry and a black layer forms at the kernel base.",
                "notes_vi": "Thu gom thân lá bị bệnh cháy lá lớn và gỉ sắt sau thu hoạch để ủ vôi hoặc tiêu hủy, không để tàn dư lưu tồn qua vụ sau.",
                "notes_en": "Compost with lime or destroy infected stalks/leaves after harvest to eliminate overwintering inoculum.",
                "common_diseases": [
                    "Bệnh cháy lá lớn hại ngô (Đốm lá lớn)",
                    "Bệnh rỉ sắt hại ngô"
                ]
            }
        ]
    },
    {
        "crop": "Cà phê",
        "scientific_name": "Coffea canephora / Coffea arabica",
        "source_agency": "Viện KHKT Nông lâm nghiệp Tây Nguyên (WASI) & Trung tâm Khuyến nông Quốc gia",
        "summary_vi": "Cây công nghiệp chủ lực vùng Tây Nguyên & Tây Bắc, cần đất đỏ bazan tầng dày >70cm, thoát nước tốt, có đai rừng chắn gió và cây che bóng hợp lý (sầu riêng, bơ, muồng đen).",
        "summary_en": "Key industrial crop requiring deep (>70cm), well-drained basaltic soil, windbreaks, and intercropped shade trees.",
        "stages": [
            {
                "stage_number": 1,
                "title_vi": "Giai đoạn 1: Làm đất, Cải tạo tái canh & Trồng mới đầu mùa mưa",
                "title_en": "Stage 1: Land Preparation, Replanting Rotation & Planting",
                "timing_vi": "Tháng 5 – Tháng 7 (Đầu mùa mưa)",
                "timing_en": "May – July (Early rainy season)",
                "care_vi": "Với vườn tái canh phải luân canh cây họ đậu 1–2 năm và xử lý tuyến trùng, nấm đất. Đào hố 60x60x60cm, bón lót 15–20kg phân chuồng hoai + Trichoderma + 0.5kg lân nung chảy + 0.3kg vôi. Chọn giống kháng gỉ sắt (TR4, TR9, TRS1, THA1), trồng mật độ 3x3m (Robusta) hoặc 2x1.5m (Arabica).",
                "care_en": "For replanted orchards, rotate legumes for 1–2 years first. Dig 60x60x60cm pits with 15–20kg Trichoderma manure + 0.5kg fused phosphate + 0.3kg lime. Plant rust-resistant clones (TR4, TR9, TRS1, THA1).",
                "notes_vi": "Vườn ươm và cây con mới trồng nếu thiếu che bóng hoặc thừa đạm rất dễ bị bệnh đốm mắt cua làm rụng lá hàng loạt.",
                "notes_en": "Unshaded nursery and young field plants over-fertilized with N suffer severe brown eye spot defoliation.",
                "common_diseases": [
                    "Bệnh đốm mắt cua cà phê",
                    "Bệnh gỉ sắt cà phê"
                ]
            },
            {
                "stage_number": 2,
                "title_vi": "Giai đoạn 2: Phân hóa mầm hoa, Xiết nước & Tưới kích thích ra hoa",
                "title_en": "Stage 2: Flower Bud Differentiation, Dry Stress & Blossom Irrigation",
                "timing_vi": "Tháng 1 – Tháng 3 (Mùa khô)",
                "timing_en": "January – March (Dry season)",
                "care_vi": "Sau thu hoạch, để cây trải qua thời kỳ khô hạn sinh lý cho đến khi mầm hoa phân hóa hoàn toàn (mầm hoa dài 1–1.5cm như mỏ sẻ, lá hơi héo vào buổi trưa). Tiến hành tưới nước đợt 1 đủ lượng (350–450 lít/gốc hoặc tưới tiết kiệm) để hoa nở trắng đồng loạt sau 7–10 ngày.",
                "care_en": "Allow physiological dry stress post-harvest until flower buds reach 1–1.5cm ('sparrow beak' stage). Apply blossom irrigation to trigger synchronized flowering within 7–10 days.",
                "notes_vi": "Không tưới quá sớm khi mầm hoa chưa phân hóa đủ (gây hoa chanh) hoặc tưới không đủ nước làm hoa nở lọt sọt.",
                "notes_en": "Do not irrigate prematurely before bud differentiation completes, or apply insufficient water causing uneven bloom.",
                "common_diseases": [
                    "Bệnh gỉ sắt cà phê"
                ]
            },
            {
                "stage_number": 3,
                "title_vi": "Giai đoạn 3: Đậu quả non, Nuôi cành dự trữ & Đầu mùa mưa",
                "title_en": "Stage 3: Young Berry Set, Reserve Branch Growth & Early Rainy Season",
                "timing_vi": "Tháng 4 – Tháng 7",
                "timing_en": "April – July",
                "care_vi": "Khi mưa xuống, tiến hành vặt chồi vượt định kỳ 20–30 ngày/lần và để lại cành dự trữ cho vụ sau. Bón phân mùa mưa đợt 1 và đợt 2 (NPK 16-16-8+TE) kết hợp phun bổ sung Bo, Kẽm chống rụng quả non sinh lý.",
                "care_en": "Remove water sprouts every 20–30 days and select reserve branches for next season. Apply 1st and 2nd rainy-season NPK (16-16-8+TE) dressings plus foliar B and Zn to prevent June drop.",
                "notes_vi": "Kiểm tra mặt dưới lá bánh tẻ đầu mùa mưa để phát hiện sớm các chấm vàng trong suốt của bệnh gỉ sắt.",
                "notes_en": "Inspect the undersides of mature leaves in early rainy season for translucent yellow oil-spots of coffee leaf rust.",
                "common_diseases": [
                    "Bệnh gỉ sắt cà phê",
                    "Bệnh đốm mắt cua cà phê",
                    "Bệnh khô cành khô quả cà phê (Thán thư)"
                ]
            },
            {
                "stage_number": 4,
                "title_vi": "Giai đoạn 4: Quả lớn nhanh, Vô nhân & Cao điểm mùa mưa",
                "title_en": "Stage 4: Rapid Berry Expansion, Bean Filling & Peak Monsoon",
                "timing_vi": "Tháng 8 – Tháng 10",
                "timing_en": "August – October",
                "care_vi": "Cây tiêu thụ dinh dưỡng cao nhất trong năm để nuôi nhân cà phê và nuôi cành dự trữ. Bón phân đợt 3 và đợt 4 giàu Đạm và Kali (NPK 16-8-16+TE hoặc 17-7-17). Rong tỉa cây che bóng để vườn thông thoáng trong những tháng mưa dầm.",
                "care_en": "Peak nutrient demand for bean filling and branch growth. Apply 3rd and 4th NPK dressings rich in N and K (16-8-16+TE) and thin shade trees to improve aeration during heavy monsoon rains.",
                "notes_vi": "Mưa dầm kéo dài kết hợp cây thiếu Kali/Đạm làm nấm Thán thư tấn công đốt cành và chùm quả gây rụng quả hàng loạt.",
                "notes_en": "Prolonged monsoon rains combined with K/N deficiency trigger severe anthracnose twig dieback and berry drop.",
                "common_diseases": [
                    "Bệnh khô cành khô quả cà phê (Thán thư)",
                    "Bệnh gỉ sắt cà phê",
                    "Bệnh đốm mắt cua cà phê"
                ]
            },
            {
                "stage_number": 5,
                "title_vi": "Giai đoạn 5: Thu hoạch quả chín & Cắt cành vệ sinh sau thu hoạch",
                "title_en": "Stage 5: Selective Ripe Harvest & Post-Harvest Pruning",
                "timing_vi": "Tháng 11 – Tháng 1 năm sau",
                "timing_en": "November – January",
                "care_vi": "Thu hái nhiều đợt khi tỷ lệ quả chín đạt >85–90%, không tuốt xanh làm gãy dập đốt cành mang hoa vụ tới. Ngay sau thu hoạch, cắt bỏ toàn bộ cành khô, cành sâu bệnh, cành tăm, cành sát đất và phun thuốc gốc Đồng rửa vườn.",
                "care_en": "Harvest selectively when >85–90% of berries are ripe; avoid stripping green berries which damages flowering nodes. Immediately prune dead/diseased/skirt branches and apply a post-harvest copper cleanup spray.",
                "notes_vi": "Bổ sung phân hữu cơ hoai mục + vôi bột sau thu hoạch giúp cây phục hồi nhanh trước khi bước vào kỳ phân hóa mầm hoa.",
                "notes_en": "Apply composted manure and lime after harvest to restore tree vigor before flower bud differentiation.",
                "common_diseases": [
                    "Bệnh khô cành khô quả cà phê (Thán thư)",
                    "Bệnh gỉ sắt cà phê"
                ]
            }
        ]
    },
    {
        "crop": "Hồ tiêu/Ớt",
        "scientific_name": "Piper nigrum / Capsicum annuum",
        "source_agency": "Viện KHKT Nông lâm nghiệp Tây Nguyên (WASI) & Cục Bảo vệ thực vật",
        "summary_vi": "Nhóm cây gia vị có bộ rễ cực kỳ mẫn cảm với ngập úng và nấm đất (Phytophthora); yêu cầu canh tác trên đất thoát nước tuyệt đối, dùng trụ sống và quản lý sinh học vùng rễ.",
        "summary_en": "High-value spice crops with root systems extremely sensitive to waterlogging and soil-borne Phytophthora; require raised drainage, living standards, and biological rhizosphere management.",
        "stages": [
            {
                "stage_number": 1,
                "title_vi": "Giai đoạn 1: Thiết kế thoát nước, Trồng trụ sống & Xuống giống",
                "title_en": "Stage 1: Drainage Engineering, Living Standards & Planting",
                "timing_vi": "Đầu mùa mưa (Hồ tiêu) hoặc Vụ Đông Xuân / Xuân Hè (Ớt)",
                "timing_en": "Early rainy season (Black pepper) or Winter-Spring (Chili)",
                "care_vi": "Đào hệ thống rãnh thoát nước sâu 40–50cm bao quanh lô và giữa các hàng. Bón lót phân hữu cơ vi sinh giàu nấm đối kháng Trichoderma + vi khuẩn Bacillus subtilis. Với hồ tiêu: ưu tiên trồng trụ sống (keo dậu, muồng đen, lồng mức); với ớt: lên luống cao 25–30cm phủ màng nông nghiệp.",
                "care_en": "Construct 40–50cm drainage trenches around blocks and inter-rows. Apply bio-organic manure enriched with Trichoderma and Bacillus subtilis. Use living support trees for black pepper and plastic-mulched 25–30cm raised beds for chili.",
                "notes_vi": "Tuyệt đối không lấy dây giống từ vườn tiêu đã nhiễm bệnh chết nhanh, chết chậm hoặc chọn hạt ớt từ quả bị bệnh thán thư.",
                "notes_en": "Never take cuttings from Phytophthora-infected pepper gardens or save seeds from anthracnose-infected chili fruits.",
                "common_diseases": [
                    "Bệnh chết nhanh hồ tiêu (Thối gốc rễ)"
                ]
            },
            {
                "stage_number": 2,
                "title_vi": "Giai đoạn 2: Phát triển thân lá, Buộc dây / Bấm ngọn tạo tán",
                "title_en": "Stage 2: Vegetative Growth, Vine Tying & Canopy Pinching",
                "timing_vi": "Giai đoạn cây con & Phát triển cành nhánh",
                "timing_en": "Juvenile & Vegetative branching stage",
                "care_vi": "Hồ tiêu: buộc dây thân chính áp sát trụ, thực hiện đôn dây hoặc bấm ngọn ở độ cao 60–80cm để phát triển cành ác (cành quả) từ dưới gốc lên. Ớt: tỉa bỏ toàn bộ chồi nách dưới chạc chữ Y đầu tiên để gốc thông thoáng. Giữ thảm cỏ tự nhiên giữa hàng (cắt ngắn 10cm, không xới đất làm đứt rễ).",
                "care_en": "Pepper: tie main vines tightly to standards and tip/coil at 60–80cm to force lower fruiting laterals. Chili: prune all axillary shoots below the first Y-fork. Maintain a mowed grass cover between rows without root-damaging tillage.",
                "notes_vi": "Cắt tỉa toàn bộ cành lươn, dây thân bò sát mặt đất (dưới 30–40cm) trước mùa mưa để ngăn nước mưa bắn bào tử Phytophthora từ đất lên lá.",
                "notes_en": "Prune all runner shoots and lower foliage (<30–40cm from ground) before the rainy season to stop rain-splash of Phytophthora spores.",
                "common_diseases": [
                    "Bệnh chết nhanh hồ tiêu (Thối gốc rễ)",
                    "Bệnh thán thư hại ớt và hồ tiêu"
                ]
            },
            {
                "stage_number": 3,
                "title_vi": "Giai đoạn 3: Phân hóa mầm hoa, Ra gié hoa / Nở hoa & Đậu quả",
                "title_en": "Stage 3: Spike Emergence / Flowering & Fruit Set",
                "timing_vi": "Tháng 5–7 (Hồ tiêu ra gié) / 35–50 ngày sau trồng (Ớt)",
                "timing_en": "May–Jul (Pepper spiking) / 35–50 DAT (Chili flowering)",
                "care_vi": "Bón phân giàu Lân, Kali, Canxi và Bo trước và trong khi ra gié hoa để tăng tỷ lệ thụ phấn, chống rụng gié/rụng hoa. Rong tỉa cành cây trụ sống để ánh sáng tán xạ đạt 60–70%.",
                "care_en": "Supply P, K, Ca, and Boron before and during flowering/spiking to prevent spike/blossom drop. Prune living standard canopies to allow 60–70% filtered sunlight.",
                "notes_vi": "Thời điểm ra gié hoa của hồ tiêu trùng với đầu mùa mưa: cần phun/tưới phòng chế phẩm Phosphonate (Lân 2 chiều) kết hợp Trichoderma bảo vệ cổ rễ.",
                "notes_en": "Pepper spiking coincides with early monsoon rains: apply preventive Potassium Phosphonate trunk/foliar sprays and Trichoderma root drenches.",
                "common_diseases": [
                    "Bệnh chết nhanh hồ tiêu (Thối gốc rễ)",
                    "Bệnh thán thư hại ớt và hồ tiêu"
                ]
            },
            {
                "stage_number": 4,
                "title_vi": "Giai đoạn 4: Nuôi chuỗi hạt / Nuôi quả lớn trong mùa mưa ẩm",
                "title_en": "Stage 4: Berry Filling / Fruit Expansion in Humid Weather",
                "timing_vi": "Tháng 8 – Tháng 12 (Hồ tiêu) / Giai đoạn mang quả rộ (Ớt)",
                "timing_en": "Aug–Dec (Pepper) / Peak fruiting (Chili)",
                "care_vi": "Chia nhỏ lượng phân NPK giàu Kali bón nhiều lần (tránh bón đạm urê đơn làm vỏ quả mỏng, dễ nứt và mẫn cảm với nấm thán thư). Bổ sung Canxi-Bo định kỳ 10–15 ngày/lần giúp cuống gié và vỏ quả cứng chắc.",
                "care_en": "Split high-K NPK into small, frequent applications (avoid straight urea which softens fruit skin and invites anthracnose). Apply foliar Ca-B every 10–15 days to strengthen fruit walls and pedicels.",
                "notes_vi": "Nếu phát hiện trụ tiêu héo rũ chết nhanh hoặc quả ớt thối lõm đồng tiền màu da cam, phải thu gom tiêu hủy ngay và rắc vôi khử trùng ổ bệnh, không tưới tràn qua gốc bệnh.",
                "notes_en": "Immediately remove and lime-sanitize any Phytophthora-wilted pepper vine or anthracnose-rotted chili fruit; never flood-irrigate across infected zones.",
                "common_diseases": [
                    "Bệnh thán thư hại ớt và hồ tiêu",
                    "Bệnh chết nhanh hồ tiêu (Thối gốc rễ)"
                ]
            },
            {
                "stage_number": 5,
                "title_vi": "Giai đoạn 5: Thu hoạch, Vệ sinh vườn & Phục hồi sau thu hoạch",
                "title_en": "Stage 5: Harvest, Sanitation & Post-Harvest Recovery",
                "timing_vi": "Tháng 1 – Tháng 4 (Hồ tiêu) / Thu hái nhiều lứa (Ớt)",
                "timing_en": "Jan–Apr (Pepper) / Multi-pick harvest (Chili)",
                "care_vi": "Hồ tiêu: thu hái khi chùm quả có >5–10% quả chín đỏ (tiêu đen) hoặc >70% quả chín (tiêu sọ). Sau thu hoạch, cắt tỉa cành tăm, vệ sinh rong rêu trên thân và bón phân hữu cơ hoai mục + lân + vôi bột phục hồi sức cây.",
                "care_en": "Harvest black pepper when spikes show 5–10% red berries. Post-harvest, prune weak twigs, clean moss from trunks, and apply compost + phosphorus + lime to restore root health.",
                "notes_vi": "Không xới đất sâu quanh gốc tiêu sau thu hoạch; chỉ cào lá phủ mặt mô để bón phân hữu cơ rồi tủ lại giữ ẩm.",
                "notes_en": "Never cultivate deeply around pepper roots post-harvest; gently rake mulch aside to apply organic manure, then re-mulch.",
                "common_diseases": [
                    "Bệnh chết nhanh hồ tiêu (Thối gốc rễ)",
                    "Bệnh thán thư hại ớt và hồ tiêu"
                ]
            }
        ]
    },
    {
        "crop": "Sầu riêng",
        "scientific_name": "Durio zibethinus",
        "source_agency": "Viện Cây ăn quả miền Nam (SOFRI) & Cục Bảo vệ thực vật",
        "summary_vi": "Cây ăn quả đặc sản giá trị kinh tế rất cao (Ri6, Monthong), yêu cầu đất thoát nước hoàn hảo, pH 5.5–6.5, quản lý chặt chẽ 2–3 cơi đọt khỏe trước khi làm bông và phòng nấm Phytophthora suốt mùa mưa.",
        "summary_en": "High-value tropical fruit tree (Ri6, Monthong) requiring superior drainage, pH 5.5–6.5, strict management of 2–3 healthy leaf flushes prior to flowering, and year-round Phytophthora defense.",
        "stages": [
            {
                "stage_number": 1,
                "title_vi": "Giai đoạn 1: Đắp mô, Trồng mới & Kiến thiết bộ khung tán (1–3 năm đầu)",
                "title_en": "Stage 1: Mound Construction, Planting & Structural Training (Years 1–3)",
                "timing_vi": "Năm thứ 1 đến năm thứ 3 sau trồng",
                "timing_en": "Years 1 to 3 after planting",
                "care_vi": "Đắp mô cao 50–80cm, đường kính mô 1.2–1.5m (mở rộng mô hàng năm theo tán cây), mật độ 8x8m hoặc 8x10m. Bón phân hữu cơ vi sinh Trichoderma định kỳ 3 tháng/lần. Tỉa cành tạo tán thông thoáng từ năm thứ 2, giữ các cành ngang khỏe mạnh cách nhau 25–30cm trên thân chính.",
                "care_en": "Build mounds 50–80cm high (expanding annually with the canopy) at 8x8m or 8x10m spacing. Apply Trichoderma bio-organic fertilizer quarterly and train horizontal scaffold branches spaced 25–30cm apart.",
                "notes_vi": "Cây con 1–2 năm đầu cần che nắng 30–40% vào mùa khô và bảo vệ tuyệt đối các đợt đọt non khỏi rầy nhảy.",
                "notes_en": "Provide 30–40% shade for 1–2 year-old saplings in the dry season and protect every young flush from psyllids.",
                "common_diseases": [
                    "Rầy nhảy hại sầu riêng (Rầy phấn)",
                    "Bệnh cháy lá chết ngọn sầu riêng",
                    "Bệnh thán thư lá sầu riêng"
                ]
            },
            {
                "stage_number": 2,
                "title_vi": "Giai đoạn 2: Phục hồi sau thu hoạch & Nuôi 2–3 cơi đọt thuần thục",
                "title_en": "Stage 2: Post-Harvest Recovery & Cultivating 2–3 Mature Leaf Flushes",
                "timing_vi": "Kéo dài 3 – 4.5 tháng sau thu hoạch vụ trước",
                "timing_en": "3 – 4.5 months following previous harvest",
                "care_vi": "Rửa vườn bằng thuốc gốc Đồng hoặc vôi lưu huỳnh, cắt bỏ cành khô/cành bơi trong tán. Bón phân hữu cơ hoai mục (15–25kg/gốc) + Humic + NPK giàu Đạm - Lân (30-10-10 hoặc 20-20-15) để thúc 2–3 cơi đọt ra đồng loạt, lá to dày xanh bóng dự trữ nhựa cho vụ bông.",
                "care_en": "Sanitize the canopy with copper, prune dead/water shoots, and apply 15–25kg compost + Humic acid + high N-P NPK to grow 2–3 vigorous, thick leaf flushes before flower induction.",
                "notes_vi": "Khi mũi giáo vừa nhú đến khi lá mở là lúc Rầy nhảy tấn công dữ dội nhất; nếu để rụng lá cơi đọt cuối cây sẽ bị 'cháy lá' khi mang trái.",
                "notes_en": "From spear-leaf emergence to leaf unfolding is the peak attack window for durian psyllids; losing the final flush causes severe leaf scorch during fruiting.",
                "common_diseases": [
                    "Rầy nhảy hại sầu riêng (Rầy phấn)",
                    "Bệnh cháy lá chết ngọn sầu riêng",
                    "Bệnh thán thư lá sầu riêng",
                    "Bệnh đốm rong (Tảo đỏ) hại lá và cành sầu riêng"
                ]
            },
            {
                "stage_number": 3,
                "title_vi": "Giai đoạn 3: Làm bông (Phân hóa mầm hoa), Xổ nhụy & Đậu trái non",
                "title_en": "Stage 3: Flower Induction, Anthesis & Young Fruit Set",
                "timing_vi": "Từ lúc nhú mắt cua đến xổ nhụy (50–60 ngày)",
                "timing_en": "From 'crab-eye' bud emergence to anthesis (50–60 days)",
                "care_vi": "Khi lá cơi cuối vừa lụa, bón phân Lân + Kali cao (Lân văn điển + K2SO4, phun MKP 10-60-10) và xiết nước tạo khô hạn 10–20 ngày đến khi mắt cua trên dạ cành sáng rõ dài 2–3cm thì tưới nhấp nước trở lại. Tỉa bông 2 đợt để giữ 1–2 chùm bông/vị trí cách nhau 20–25cm; bổ sung Canxi-Bo trước khi xổ nhụy.",
                "care_en": "Once the final flush matures, apply high P-K + foliar MKP and withhold water for 10–20 days until 'crab-eye' flower buds reach 2–3cm, then resume light irrigation. Thin blossom clusters in 2 rounds and spray Ca-B before anthesis.",
                "notes_vi": "Kiểm soát chặn đọt (không để cây đi đọt non trùng lúc xổ nhụy và trái non <45 ngày) để tránh hiện tượng cạnh tranh dinh dưỡng gây rụng bông, rụng trái hàng loạt.",
                "notes_en": "Prevent vegetative flushing during anthesis and the first 45 days of fruit development to avoid massive physiological fruit drop.",
                "common_diseases": [
                    "Bệnh thán thư lá sầu riêng",
                    "Rầy nhảy hại sầu riêng (Rầy phấn)",
                    "Bệnh cháy lá chết ngọn sầu riêng"
                ]
            },
            {
                "stage_number": 4,
                "title_vi": "Giai đoạn 4: Tuyển trái, Nuôi trái lớn & Vô cơm (15–90 ngày sau đậu trái)",
                "title_en": "Stage 4: Fruit Thinning, Expansion & Aril Filling (15–90 DAA)",
                "timing_vi": "Từ 15 đến 90 ngày sau xổ nhụy",
                "timing_en": "15 to 90 days after anthesis (DAA)",
                "care_vi": "Tuyển trái qua 3 đợt (lúc trái bằng trứng gà, trứng ngỗng và 45 ngày tuổi), loại bỏ trái méo, trái đeo và giữ số lượng trái vừa sức cây (60–100 trái với cây 7–10 năm). Bón NPK cân đối (15-15-15) giai đoạn nuôi hộc và chuyển sang Kali Sunfat cao (12-11-18, K2SO4) từ 60 ngày trở đi để tránh sượng cơm.",
                "care_en": "Thin fruits in 3 stages (15, 30, and 45 DAA) to match tree capacity. Apply balanced NPK (15-15-15) during locule expansion and switch to chloride-free sulfate of potash (12-11-18, K2SO4) from 60 DAA onward to prevent physiological wet-core.",
                "notes_vi": "Tuyệt đối KHÔNG dùng phân Kali đỏ (KCl chứa Clo) vì gây sượng nước múi sầu riêng. Tỉa thưa trái mọc chùm để hạn chế Sâu đục quả ẩn nấp.",
                "notes_en": "NEVER use Muriate of Potash (KCl) on fruiting durian as chloride causes wet/hard core disorder. Separate touching fruits to deter fruit borers.",
                "common_diseases": [
                    "Sâu đục quả sầu riêng",
                    "Bệnh cháy lá chết ngọn sầu riêng",
                    "Bệnh đốm rong (Tảo đỏ) hại lá và cành sầu riêng"
                ]
            },
            {
                "stage_number": 5,
                "title_vi": "Giai đoạn 5: Chín sinh lý, Thu hoạch đạt độ khô & Vệ sinh gốc thân",
                "title_en": "Stage 5: Physiological Maturity, Dry-Matter Harvest & Trunk Care",
                "timing_vi": "95–105 ngày (Ri6) hoặc 115–125 ngày (Monthong) sau xổ nhụy",
                "timing_en": "95–105 DAA (Ri6) or 115–125 DAA (Monthong)",
                "care_vi": "Giảm tưới nước 10–15 ngày trước thu hoạch để cơm sầu riêng khô dẻo, lên màu vàng đậm. Thu hoạch đúng độ tuổi (kiểm tra rãnh múi, gai nở, cuống phình và độ khô chất khô đạt chuẩn xuất khẩu), không để trái chạm đất.",
                "care_en": "Reduce irrigation 10–15 days pre-harvest for creamy, dry arils. Harvest at proper maturity (check suture lines, spine pliability, abscission ring, and dry matter %) without letting fruits touch soil.",
                "notes_vi": "Kiểm tra kỹ thân chính và cổ rễ sau mùa mang trái nặng; nếu có vết xì mủ nước màu nâu đỏ của Phytophthora phải cạo xử lý thuốc lưu dẫn ngay.",
                "notes_en": "Inspect main trunks and root collars closely after heavy cropping; treat any reddish-brown Phytophthora gummosis lesions immediately.",
                "common_diseases": [
                    "Sâu đục quả sầu riêng",
                    "Bệnh cháy lá chết ngọn sầu riêng",
                    "Bệnh đốm rong (Tảo đỏ) hại lá và cành sầu riêng"
                ]
            }
        ]
    },
    {
        "crop": "Cà chua",
        "scientific_name": "Solanum lycopersicum",
        "source_agency": "Viện Nghiên cứu Rau quả (FAVRI) & Trung tâm Khuyến nông Quốc gia",
        "summary_vi": "Cây rau ăn quả giá trị cao trồng chủ lực vụ Đông Xuân và Xuân Hè; đòi hỏi đất thịt nhẹ thoát nước tốt (pH 6.0–6.8), làm giàn chữ A thông thoáng và quản lý nghiêm ngặt bọ phấn trắng cùng bệnh mốc sương.",
        "summary_en": "High-value solanaceous vegetable requiring well-drained sandy loam (pH 6.0–6.8), A-frame staking, and strict management of whitefly vectors and late blight.",
        "stages": [
            {
                "stage_number": 1,
                "title_vi": "Giai đoạn 1: Vườn ươm khay bầu nhà lưới, Làm đất & Trồng cây con",
                "title_en": "Stage 1: Screenhouse Tray Nursery, Bed Prep & Transplanting",
                "timing_vi": "Ươm 20–25 ngày & 0–10 ngày sau trồng",
                "timing_en": "20–25 days nursery & 0–10 days after transplanting (DAT)",
                "care_vi": "Ươm cây con trong khay xơ dừa có nhà lưới chắn côn trùng (ngăn bọ phấn trắng truyền virus TYLCV từ giai đoạn vườn ươm). Lên luống cao 25–30cm, rộng 1.1–1.2m, bón lót 20 tấn phân hữu cơ hoai + Trichoderma + 500kg lân + 500kg vôi/ha và phủ màng bạc nông nghiệp. Trồng hàng đôi mật độ 22.000–25.000 cây/ha.",
                "care_en": "Raise seedlings in insect-proof screenhouse trays to block whitefly TYLCV transmission. Form 25–30cm raised beds with Trichoderma compost + P + lime covered with silver reflective mulch; transplant at 22,000–25,000 plants/ha.",
                "notes_vi": "Không trồng cà chua trên đất vừa trồng cây họ Cà (cà chua, khoai tây, ớt, cà tím) vụ trước để cắt nguồn bệnh tồn lưu.",
                "notes_en": "Rotate away from fields previously planted with Solanaceae (tomato, potato, chili, eggplant).",
                "common_diseases": [
                    "Bệnh virus xoăn vàng lá cà chua (TYLCV)"
                ]
            },
            {
                "stage_number": 2,
                "title_vi": "Giai đoạn 2: Hồi xanh – Phát triển thân lá, Cắm giàn & Tỉa nhánh",
                "title_en": "Stage 2: Vegetative Growth, Staking & Suckering (10–30 DAT)",
                "timing_vi": "10 – 30 ngày sau trồng",
                "timing_en": "10 – 30 days after transplanting",
                "care_vi": "Bón thúc lần 1 (10–15 ngày sau trồng) bằng phân NPK hòa nước tưới gốc. Khi cây cao 30–40cm tiến hành cắm cọc làm giàn chữ A và buộc thân. Tỉa bỏ toàn bộ các chồi nách dưới chùm hoa thứ nhất vào buổi sáng nắng ráo (chừa 1 thân chính hoặc 2 thân tùy giống).",
                "care_en": "Apply 1st fertigation at 10–15 DAT. Install A-frame stakes when plants reach 30–40cm and prune axillary suckers below the first flower cluster on sunny mornings.",
                "notes_vi": "Treo bẫy dính màu vàng (40–50 bẫy/1.000m2) ngay trên ngọn cây để giám sát và bắt bọ phấn trắng truyền bệnh xoăn vàng lá.",
                "notes_en": "Hang yellow sticky traps (40–50 traps/1,000m2) just above the canopy to trap whitefly vectors.",
                "common_diseases": [
                    "Bệnh virus xoăn vàng lá cà chua (TYLCV)",
                    "Bệnh đốm vòng cà chua (Cháy sớm)"
                ]
            },
            {
                "stage_number": 3,
                "title_vi": "Giai đoạn 3: Ra hoa rộ & Đậu quả các tầng chùm (30–50 ngày sau trồng)",
                "title_en": "Stage 3: Full Bloom & Truss Fruit Set (30–50 DAT)",
                "timing_vi": "30 – 50 ngày sau trồng",
                "timing_en": "30 – 50 days after transplanting",
                "care_vi": "Bón thúc lần 2 tăng cường Lân, Kali và phun bổ sung Canxi-Bo qua lá để hoa thụ phấn tốt, chống rụng hoa và phòng thối đít quả sinh lý. Tỉa bỏ bớt hoa dị dạng ở cuối chùm (chỉ giữ 4–6 quả đều nhau/chùm).",
                "care_en": "Apply 2nd top-dressing rich in P-K and spray foliar Ca-B to enhance pollination and prevent blossom-end rot. Thin trusses to 4–6 uniform fruits per cluster.",
                "notes_vi": "Khi trời chuyển lạnh (15–22°C), sương mù dày và mưa phùn cần phun phòng sớm bệnh mốc sương (héo muộn) vì bệnh có thể hủy diệt ruộng trong 5–7 ngày.",
                "notes_en": "When cool (15–22°C), foggy, drizzly weather arrives, apply preventive late blight protection immediately as Phytophthora infestans can destroy a crop within 5–7 days.",
                "common_diseases": [
                    "Bệnh mốc sương cà chua (Héo muộn)",
                    "Bệnh đốm vòng cà chua (Cháy sớm)",
                    "Bệnh virus xoăn vàng lá cà chua (TYLCV)"
                ]
            },
            {
                "stage_number": 4,
                "title_vi": "Giai đoạn 4: Nuôi quả lớn & Chuyển màu (50–75 ngày sau trồng)",
                "title_en": "Stage 4: Fruit Expansion & Breaker Stage (50–75 DAT)",
                "timing_vi": "50 – 75 ngày sau trồng",
                "timing_en": "50 – 75 days after transplanting",
                "care_vi": "Bón thúc lần 3 và 4 với hàm lượng Kali cao (NPK 12-12-17+TE, K2SO4) giúp quả to chắc, lên màu đỏ đẹp và tăng độ đường. Tỉa bỏ các lá già chân gốc dưới chùm quả đang chín để tạo độ thông thoáng tối đa cho mặt luống.",
                "care_en": "Apply 3rd and 4th high-K dressings (12-12-17+TE, K2SO4) for firm, deep-red fruits. Remove senescent lower leaves beneath ripening clusters to maximize under-canopy airflow.",
                "notes_vi": "Giữ ẩm đất ổn định 70–80%, tránh để đất khô hạn lâu ngày rồi tưới ngập đột ngột làm quả bị nứt vỏ và nhiễm nấm đốm vòng, mốc sương.",
                "notes_en": "Keep soil moisture steady at 70–80%; sudden heavy irrigation after dry spells splits fruits and invites early/late blight.",
                "common_diseases": [
                    "Bệnh mốc sương cà chua (Héo muộn)",
                    "Bệnh đốm vòng cà chua (Cháy sớm)"
                ]
            },
            {
                "stage_number": 5,
                "title_vi": "Giai đoạn 5: Thu hoạch nhiều lứa & Vệ sinh đồng ruộng",
                "title_en": "Stage 5: Multi-Pick Harvest & Field Sanitation (75–120 DAT)",
                "timing_vi": "75 – 120 ngày sau trồng",
                "timing_en": "75 – 120 days after transplanting",
                "care_vi": "Thu hái cách nhật khi quả chuyển hồng (vận chuyển xa) hoặc chín đỏ (tiêu thụ gần). Sau mỗi đợt thu hái lớn, tưới bổ sung phân Kali-Canxi hòa tan để nuôi các tầng quả phía trên.",
                "care_en": "Harvest every 2–3 days at breaker stage (long transport) or red-ripe stage (local market). Fertigate soluble K-Ca after major picks to sustain upper trusses.",
                "notes_vi": "Tuyệt đối tuân thủ thời gian cách ly thuốc BVTV. Cuối vụ thu gom toàn bộ dây cà chua và quả rụng đem tiêu hủy xa ruộng.",
                "notes_en": "Strictly observe Pre-Harvest Intervals (PHI). At crop end, remove and destroy all haulms and culled fruits.",
                "common_diseases": [
                    "Bệnh mốc sương cà chua (Héo muộn)",
                    "Bệnh đốm vòng cà chua (Cháy sớm)"
                ]
            }
        ]
    },
    {
        "crop": "Khoai tây",
        "scientific_name": "Solanum tuberosum",
        "source_agency": "Viện Cây lương thực và Cây thực phẩm (FCRI) & Trung tâm Khuyến nông Quốc gia",
        "summary_vi": "Cây lấy củ vụ Đông ưa thời tiết mát lạnh (16–22°C), đất cát pha hoặc thịt nhẹ tơi xốp sau vụ lúa mùa; cần củ giống sạch bệnh và vun luống cao chống xanh củ, phòng bệnh mốc sương.",
        "summary_en": "Winter tuber crop thriving at 16–22°C in sandy loam after monsoon rice; requires certified seed tubers, high hilling, and strict late blight protection.",
        "stages": [
            {
                "stage_number": 1,
                "title_vi": "Giai đoạn 1: Chọn củ giống mầm mập, Làm đất & Trồng (0–15 ngày)",
                "title_en": "Stage 1: Seed Tuber Sprouting, Bed Prep & Planting (0–15 DAP)",
                "timing_vi": "0 – 15 ngày sau trồng (Tháng 10–11 vụ Đông)",
                "timing_en": "0 – 15 days after planting (Oct–Nov Winter crop)",
                "care_vi": "Chọn củ giống nguyên chủng/xác nhận (Solara, Marabel, Sinora, Atlantic) có 2–3 mầm ngắn mập (1–1.5cm), không cắt củ khi thời tiết ẩm ướt. Lên luống cao 25–30cm, bón lót 15–20 tấn phân chuồng hoai + Trichoderma + 100% Lân + 40% Đạm + 40% Kali, đặt củ sâu 5–7cm rồi phủ rơm rạ mặt luống.",
                "care_en": "Select certified seed tubers with 2–3 stout sprouts (1–1.5cm). Form 25–30cm raised beds with 15–20t Trichoderma manure + 100% P + 40% N + 40% K, plant 5–7cm deep, and mulch with rice straw.",
                "notes_vi": "Loại bỏ triệt để mọi củ giống có vết thối nâu xám trên vỏ (nguồn bệnh mốc sương khởi phát sớm ngoài đồng).",
                "notes_en": "Strictly cull any seed tuber showing brownish-grey sunken lesions (primary inoculum of late blight).",
                "common_diseases": [
                    "Bệnh mốc sương khoai tây (Héo muộn)"
                ]
            },
            {
                "stage_number": 2,
                "title_vi": "Giai đoạn 2: Mọc mầm – Cây con phát triển thân lá (15–30 ngày)",
                "title_en": "Stage 2: Emergence & Early Canopy Growth (15–30 DAP)",
                "timing_vi": "15 – 30 ngày sau trồng",
                "timing_en": "15 – 30 days after planting",
                "care_vi": "Khi cây mọc cao 15–20cm, tiến hành tỉa bớt mầm yếu (chỉ giữ 3–4 thân chính khỏe/khóm). Bón thúc lần 1 (40% Đạm + 30% Kali) kết hợp xới xáo phá váng và vun gốc lần 1.",
                "care_en": "When shoots reach 15–20cm, thin weak stems (keep 3–4 main stems/hill). Apply 1st top-dressing (40% N + 30% K) with weeding and first hilling.",
                "notes_vi": "Giữ độ ẩm đất 70–75%, tưới rãnh ngập 1/2 luống rồi tháo cạn ngay, tuyệt đối không để ngập luống.",
                "notes_en": "Maintain 70–75% soil moisture via furrow irrigation up to half bed height, then drain immediately.",
                "common_diseases": [
                    "Bệnh mốc sương khoai tây (Héo muộn)"
                ]
            },
            {
                "stage_number": 3,
                "title_vi": "Giai đoạn 3: Đứng cây – Ra tia củ & Hình thành củ non (30–45 ngày)",
                "title_en": "Stage 3: Stolon Initiation & Tuberization (30–45 DAP)",
                "timing_vi": "30 – 45 ngày sau trồng",
                "timing_en": "30 – 45 days after planting",
                "care_vi": "Bón thúc lần 2 (20% Đạm + 30% Kali còn lại) và vun luống cao tối đa lần cuối trước khi tán lá giao nhau để tia củ phát triển trong bóng tối, không bị lộ ra ánh sáng hóa xanh (chứa độc tố Solanine).",
                "care_en": "Apply final top-dressing (20% N + 30% K) and perform high final hilling before canopy closure so stolons form tubers in darkness without greening.",
                "notes_vi": "Giai đoạn khép tán trùng các đợt không khí lạnh kèm mưa phùn/sương muối cuối tháng 12 – tháng 1: cần phun phòng bệnh mốc sương định kỳ.",
                "notes_en": "Canopy closure coincides with cold wet fronts in Dec–Jan: apply preventive late blight sprays proactively.",
                "common_diseases": [
                    "Bệnh mốc sương khoai tây (Héo muộn)"
                ]
            },
            {
                "stage_number": 4,
                "title_vi": "Giai đoạn 4: Phình to củ mạnh & Tích lũy tinh bột (45–75 ngày)",
                "title_en": "Stage 4: Rapid Tuber Bulking & Starch Accumulation (45–75 DAP)",
                "timing_vi": "45 – 75 ngày sau trồng",
                "timing_en": "45 – 75 days after planting",
                "care_vi": "Duy trì ẩm độ đất ổn định 75–80% và phun bổ sung Kali-Vi lượng qua lá giúp vận chuyển tinh bột từ lá xuống củ nhanh. Kiểm tra đồng ruộng mỗi sáng sớm khi còn sương để phát hiện sớm vết bệnh mốc sương ở rìa lá.",
                "care_en": "Keep soil moisture at 75–80% and apply foliar K-micronutrients to accelerate starch translocation to tubers. Scout every morning for water-soaked leaf margin lesions.",
                "notes_vi": "Nếu có mưa làm lở luống phải vét rãnh đắp kín mặt luống ngay để ngăn bào tử nấm mốc sương từ lá rửa trôi xuống gây thối củ dưới đất.",
                "notes_en": "Repair eroded beds immediately after rain so late blight sporangia cannot wash down from foliage to infect underground tubers.",
                "common_diseases": [
                    "Bệnh mốc sương khoai tây (Héo muộn)"
                ]
            },
            {
                "stage_number": 5,
                "title_vi": "Giai đoạn 5: Chín sinh lý, Làm vỏ củ cứng & Thu hoạch (75–90 ngày)",
                "title_en": "Stage 5: Vine Senescence, Skin Set & Harvest (75–90 DAP)",
                "timing_vi": "75 – 90 ngày sau trồng",
                "timing_en": "75 – 90 days after planting",
                "care_vi": "Ngừng tưới nước trước thu hoạch 10–15 ngày. Nếu thân lá bị mốc sương cuối vụ, cần cắt bỏ toàn bộ phần thân lá trên mặt đất trước khi dỡ củ 7–10 ngày để vỏ củ suberin hóa dày chắc và không lây bệnh sang củ khi thu hoạch.",
                "care_en": "Stop irrigation 10–15 days pre-harvest. Cut and remove above-ground haulms 7–10 days before digging so tuber skins suberize and sporangia do not contaminate tubers at harvest.",
                "notes_vi": "Thu hoạch vào ngày nắng ráo, phân loại riêng củ lành và củ xây xát, bảo quản nơi thoáng mát tối.",
                "notes_en": "Harvest on dry sunny days, grade out damaged tubers, and cure in a cool, dark, ventilated store.",
                "common_diseases": [
                    "Bệnh mốc sương khoai tây (Héo muộn)"
                ]
            }
        ]
    },
    {
        "crop": "Chuối",
        "scientific_name": "Musa acuminata / Musa paradisiaca",
        "source_agency": "Viện Nghiên cứu Rau quả (FAVRI) & Viện KHKT Nông lâm nghiệp miền núi phía Bắc (NOMAFSI)",
        "summary_vi": "Cây ăn quả thương phẩm xuất khẩu chủ lực (Chuối già Nam Mỹ Cavendish, Chuối tiêu hồng), bắt buộc dùng cây giống nuôi cấy mô sạch bệnh, đất thoát nước tốt (pH 6.0–7.0) và quản lý nghiêm ngặt bệnh héo vàng Panama (TR4).",
        "summary_en": "Major export fruit crop (Cavendish, Tiêu hồng) requiring tissue-culture disease-free plantlets, well-drained soil (pH 6.0–7.0), and strict biosecurity against Fusarium wilt (TR4).",
        "stages": [
            {
                "stage_number": 1,
                "title_vi": "Giai đoạn 1: Chuẩn bị đất, Xử lý hố & Trồng chuối nuôi cấy mô",
                "title_en": "Stage 1: Land Prep, Pit Sanitization & Tissue-Culture Planting",
                "timing_vi": "0 – 30 ngày sau trồng (Vụ Xuân hoặc Thu)",
                "timing_en": "0 – 30 days after planting",
                "care_vi": "Đào rãnh thoát nước sâu 50cm, lên luống rộng. Đào hố 40x40x40cm, bón lót 15–20kg phân hữu cơ vi sinh giàu nấm đối kháng Trichoderma + 0.5kg lân + 0.5kg vôi bột (giữ pH đất >6.0 để ức chế nấm Fusarium). Chọn cây chuối cấy mô có 5–7 lá thật khỏe mạnh, trồng mật độ 2.000–2.200 cây/ha.",
                "care_en": "Dig 50cm drainage canals. Mix 15–20kg Trichoderma bio-compost + 0.5kg P + 0.5kg lime per pit (maintain pH >6.0 to suppress Fusarium). Plant 5–7 leaf tissue-culture plantlets at 2,000–2,200 plants/ha.",
                "notes_vi": "Tuyệt đối không tách chồi từ vườn chuối đã có tiền sử bệnh héo vàng Panama để nhân giống.",
                "notes_en": "Never propagate suckers from plantations with any history of Panama wilt (Fusarium oxysporum f.sp. cubense).",
                "common_diseases": [
                    "Bệnh héo vàng Panama hại chuối"
                ]
            },
            {
                "stage_number": 2,
                "title_vi": "Giai đoạn 2: Sinh trưởng thân giả mạnh & Quản lý chồi con (1–5 tháng)",
                "title_en": "Stage 2: Pseudostem Growth & Desuckering (Months 1–5)",
                "timing_vi": "Tháng thứ 1 đến tháng thứ 5 sau trồng",
                "timing_en": "Months 1 to 5 after planting",
                "care_vi": "Tưới nhỏ giọt giữ ẩm thường xuyên và bón thúc định kỳ 20–30 ngày/lần với tỷ lệ Đạm - Kali cao (NPK 20-10-20). Cắt tỉa định kỳ các chồi con phát sinh, chỉ chọn giữ lại 1 chồi kế cận khỏe mạnh đúng hướng cho vụ ratoon tiếp theo.",
                "care_en": "Maintain drip irrigation and fertigate every 20–30 days with high N-K (20-10-20). Regularly desucker, retaining only 1 vigorous follower sucker for the ratoon cycle.",
                "notes_vi": "Dụng cụ cắt tỉa chồi và lá phải được nhúng khử trùng bằng cồn 70% hoặc Javel giữa từng cây để không truyền nấm Panama từ cây bệnh sang cây lành.",
                "notes_en": "Disinfect desuckering and pruning knives in 70% alcohol or bleach between every plant to prevent mechanical transmission of Panama wilt.",
                "common_diseases": [
                    "Bệnh héo vàng Panama hại chuối",
                    "Bệnh đốm lá Sigatoka hại chuối"
                ]
            },
            {
                "stage_number": 3,
                "title_vi": "Giai đoạn 3: Phân hóa mầm hoa – Trổ buồng (Tháng thứ 5–7)",
                "title_en": "Stage 3: Floral Differentiation & Bunch Emergence (Months 5–7)",
                "timing_vi": "Tháng thứ 5 đến tháng thứ 7 sau trồng",
                "timing_en": "Months 5 to 7 after planting",
                "care_vi": "Tăng mạnh lượng phân Kali (K2SO4) và Canxi-Bo. Cây chuối cần tối thiểu 10–12 lá xanh hoàn chỉnh lúc trổ buồng để nuôi buồng đạt chuẩn xuất khẩu. Cắt tỉa sớm các phần lá già bị đốm Sigatoka đem ra khỏi vườn tiêu hủy.",
                "care_en": "Boost Potassium (K2SO4) and Ca-B supply. Ensure at least 10–12 functional green leaves at bunch emergence. Surgically de-leaf Sigatoka-spotted lower leaves and remove them from the field.",
                "notes_vi": "Nếu để bệnh đốm lá Sigatoka làm cháy khô còn dưới 6–8 lá xanh lúc trổ buồng, quả chuối sẽ nhỏ và chín ép sớm trên cây.",
                "notes_en": "If Sigatoka defoliation leaves fewer than 6–8 functional leaves at shooting, bunches will be undersized and ripen prematurely.",
                "common_diseases": [
                    "Bệnh đốm lá Sigatoka hại chuối",
                    "Bệnh héo vàng Panama hại chuối"
                ]
            },
            {
                "stage_number": 4,
                "title_vi": "Giai đoạn 4: Bẻ bắp (cắt hoa đực), Tuyển nải & Bao buồng nuôi quả",
                "title_en": "Stage 4: Debelling, Hand Thinning & Bunch Bagging (Months 7–9)",
                "timing_vi": "Tháng thứ 7 đến tháng thứ 9 sau trồng",
                "timing_en": "Months 7 to 9 after planting",
                "care_vi": "Sau khi nải cuối cùng nở hết 7–10 ngày, tiến hành bẻ bắp chuối (cắt bỏ hoa đực cách nải cuối 15cm), tỉa bỏ 1–2 nải kẹ dưới cùng (chỉ giữ 7–9 nải đều nhau), vặt râu đầu quả và dùng túi PE chuyên dụng bao kín buồng chuối. Cắm cọc hoặc chằng dây chống đổ ngã.",
                "care_en": "7–10 days after the last hand opens, remove the male bud (15cm below the last hand), thin 1–2 bottom false hands (keep 7–9 uniform hands), de-flower finger tips, and bag bunches with perforated PE sleeves. Prop pseudostems against wind.",
                "notes_vi": "Phun thuốc phòng nấm trước khi trùm bao buồng để quả chuối bóng đẹp, không bị ghẻ quả hay thán thư.",
                "notes_en": "Apply a protective fungicide spray right before bagging so fingers remain blemish-free.",
                "common_diseases": [
                    "Bệnh đốm lá Sigatoka hại chuối",
                    "Bệnh héo vàng Panama hại chuối"
                ]
            },
            {
                "stage_number": 5,
                "title_vi": "Giai đoạn 5: Thu hoạch buồng đạt độ đầy & Xử lý thân mẹ sau thu hoạch",
                "title_en": "Stage 5: Harvest at Target Caliph & Post-Harvest Pseudostem Management",
                "timing_vi": "85 – 110 ngày sau trổ buồng",
                "timing_en": "85 – 110 days after bunch emergence",
                "care_vi": "Thu hoạch khi quả đạt độ đầy đặn (mất gờ cạnh, độ chín 75–85%), vận chuyển bằng cáp treo hoặc đệm xốp tránh trầy xước vỏ. Sau khi cắt buồng, giữ lại đoạn thân mẹ cao 1.2–1.5m trong 30–40 ngày để chuyển dinh dưỡng nuôi chồi con kế cận, sau đó mới băm nhỏ tủ gốc cùng Trichoderma.",
                "care_en": "Harvest when fingers reach 75–85% fullness (rounded ridges), transporting gently via cableway or foam pads. Leave 1.2–1.5m of the mother pseudostem standing for 30–40 days to nourish the follower sucker before chopping and composting with Trichoderma.",
                "notes_vi": "Nếu phát hiện cây bị héo vàng Panama phải khoanh vùng, rắc vôi 2–3kg/hố và tuyệt đối không đào bới đất mang đi nơi khác.",
                "notes_en": "Quarantine any Panama-infected mat immediately with 2–3kg lime per pit and never move contaminated soil.",
                "common_diseases": [
                    "Bệnh héo vàng Panama hại chuối",
                    "Bệnh đốm lá Sigatoka hại chuối"
                ]
            }
        ]
    },
    {
        "crop": "Nhãn/Vải",
        "scientific_name": "Dimocarpus longan / Litchi chinensis",
        "source_agency": "Viện Nghiên cứu Rau quả (FAVRI) & Trung tâm Khuyến nông Quốc gia",
        "summary_vi": "Cây ăn quả đặc sản miền Bắc và ĐBSCL, cần điều khiển chính xác các đợt lộc thu trước khi khoanh vỏ/xiết nước phân hóa mầm hoa và bảo vệ chùm hoa – quả khỏi bệnh sương mai, thán thư, chổi rồng.",
        "summary_en": "Specialty subtropical fruit trees requiring precise autumn flush timing prior to flower induction and rigorous protection of panicles/fruits from downy blight, anthracnose, and witches' broom.",
        "stages": [
            {
                "stage_number": 1,
                "title_vi": "Giai đoạn 1: Phục hồi sau thu hoạch & Đón 2–3 đợt lộc Hè – Thu",
                "title_en": "Stage 1: Post-Harvest Pruning & Growing 2–3 Summer–Autumn Flushes",
                "timing_vi": "Tháng 7 – Tháng 10 (Miền Bắc) hoặc sau thu hoạch",
                "timing_en": "July – October (North) or post-harvest",
                "care_vi": "Ngay sau thu hoạch, cắt tỉa cành sâu bệnh, cành khuất tán, cành mang cuống quả và hạ độ cao tán (<3.5–4m). Bón toàn bộ phân hữu cơ hoai mục (30–50kg/cây) + 100% Lân + 50% Đạm + 30% Kali để nuôi 2–3 đợt lộc khỏe mạnh, thành thục trước tháng 11.",
                "care_en": "Immediately after harvest, prune diseased/interior branches and lower canopy height (<3.5–4m). Apply 30–50kg compost + 100% P + 50% N + 30% K to produce 2–3 vigorous flushes maturing before November.",
                "notes_vi": "Với cây nhãn: phải kiểm soát triệt để Nhện lông nhung (Eriophyes dimocarpi) ở mỗi đợt ra đọt non để ngăn chặn bệnh Chổi rồng làm biến dạng lá và chùm hoa.",
                "notes_en": "On longan, strictly control erinose mites on every young flush to prevent witches' broom symptom development.",
                "common_diseases": [
                    "Bệnh chổi rồng hại nhãn",
                    "Bệnh sương mai và thán thư hại vải, nhãn"
                ]
            },
            {
                "stage_number": 2,
                "title_vi": "Giai đoạn 2: Hãm lộc đông & Phân hóa mầm hoa (Tháng 11 – Tháng 1)",
                "title_en": "Stage 2: Winter Flush Suppression & Flower Induction (Nov – Jan)",
                "timing_vi": "Tháng 11 – Tháng 1 năm sau",
                "timing_en": "November – January",
                "care_vi": "Khi đợt lộc thu cuối cùng đã bánh tẻ chuyển xanh đậm, tiến hành xiết nước giữ khô hạn kết hợp khoanh vỏ cành cấp 1 (vải thiều, nhãn) hoặc xử lý KClO3 (nhãn vùng phía Nam) để chặn lộc đông và kích thích phân hóa mầm hoa.",
                "care_en": "Once the final autumn flush matures, withhold irrigation and perform spiral/closed girdling on primary limbs (or KClO3 soil drench for tropical longan) to suppress winter vegetative shoots and induce floral buds.",
                "notes_vi": "Nếu thấy bất kỳ chùm lộc non nào bị xoăn cụm dạng chổi rồng phải cắt sâu dưới vết bệnh 20–30cm đem đốt ngay trước khi cây ra hoa.",
                "notes_en": "Prune out any witches'-broom malformed shoot 20–30cm below the symptoms and burn immediately before flowering.",
                "common_diseases": [
                    "Bệnh chổi rồng hại nhãn"
                ]
            },
            {
                "stage_number": 3,
                "title_vi": "Giai đoạn 3: Nhú gié hoa – Nở hoa & Đậu quả non (Tháng 2 – Tháng 4)",
                "title_en": "Stage 3: Panicle Emergence, Anthesis & Fruit Set (Feb – Apr)",
                "timing_vi": "Tháng 2 – Tháng 4",
                "timing_en": "February – April",
                "care_vi": "Khi gié hoa nhú dài 5–10cm, tưới ẩm trở lại và bón thúc phân NPK cân đối + phun Bo, Canxi trước khi hoa nở. Tỉa bớt các chùm hoa quá dày hoặc quá dài để tập trung dinh dưỡng tăng tỷ lệ hoa cái đậu quả.",
                "care_en": "When panicles reach 5–10cm, resume irrigation, apply balanced NPK, and spray foliar B-Ca pre-bloom. Tip/thin overly long panicles to maximize female flower fruit set.",
                "notes_vi": "Tháng 2–3 miền Bắc thường có mưa phùn ẩm ướt >90%: phải phun phòng bệnh Sương mai và Thán thư lúc chùm hoa vươn dài (trước khi hoa nở) và ngay sau khi tắt hoa.",
                "notes_en": "Spring drizzle (>90% RH) triggers severe downy blight and anthracnose panicle rot: spray protectants during panicle elongation (pre-bloom) and immediately after petal fall.",
                "common_diseases": [
                    "Bệnh sương mai và thán thư hại vải, nhãn",
                    "Bệnh chổi rồng hại nhãn"
                ]
            },
            {
                "stage_number": 4,
                "title_vi": "Giai đoạn 4: Nuôi quả lớn & Vào cùi (Tháng 4 – Tháng 6)",
                "title_en": "Stage 4: Fruit Expansion & Aril Development (Apr – Jun)",
                "timing_vi": "Tháng 4 – Tháng 6",
                "timing_en": "April – June",
                "care_vi": "Bón thúc nuôi quả 2 đợt (sau tắt hoa 15 ngày và khi quả bắt đầu vào cùi) với hàm lượng Kali Sunfat cao (NPK 12-12-17+TE) kết hợp phun Canxi-Bo chống nứt quả khi gặp mưa rào đầu hạ. Tỉa thưa quả trong chùm, giữ 25–35 quả/chùm vải hoặc 40–60 quả/chùm nhãn.",
                "care_en": "Apply 2 fruit-bulking dressings rich in Potassium Sulfate (12-12-17+TE) plus foliar Ca-B to prevent fruit cracking during early summer rains. Thin clusters to 25–35 fruits (lychee) or 40–60 fruits (longan).",
                "notes_vi": "Bảo vệ cuống quả và vỏ quả khỏi nấm Sương mai (Peronophythora litchii) gây thối nâu ướt rụng quả hàng loạt trước thu hoạch.",
                "notes_en": "Protect fruit pedicels and pericarps against Peronophythora litchii downy blight which causes rapid brown watery fruit rot and drop.",
                "common_diseases": [
                    "Bệnh sương mai và thán thư hại vải, nhãn"
                ]
            },
            {
                "stage_number": 5,
                "title_vi": "Giai đoạn 5: Thu hoạch quả thương phẩm & Vệ sinh vườn",
                "title_en": "Stage 5: Commercial Harvest & Post-Harvest Sanitation",
                "timing_vi": "Tháng 6 – Tháng 8",
                "timing_en": "June – August",
                "care_vi": "Thu hoạch vào sáng sớm mát trời khi quả đạt độ chín và độ đường đặc trưng của giống; bẻ cả chùm kèm 1–2 lá non vừa thành thục. Phân loại, cắt tỉa quả nứt/bệnh ngay tại nhà đóng gói.",
                "care_en": "Harvest in the cool early morning at optimal Brix maturity. Cull any cracked or diseased berries immediately at the packing shed.",
                "notes_vi": "Thu gom toàn bộ quả rụng dưới gốc đem chôn vôi để tiêu diệt nhộng sâu đục cuống quả và bào tử nấm sương mai, thán thư.",
                "notes_en": "Collect all fallen fruits on the orchard floor and bury with lime to destroy fruit borer pupae and fungal inoculum.",
                "common_diseases": [
                    "Bệnh sương mai và thán thư hại vải, nhãn",
                    "Bệnh chổi rồng hại nhãn"
                ]
            }
        ]
    },
    {
        "crop": "Xoài",
        "scientific_name": "Mangifera indica",
        "source_agency": "Viện Cây ăn quả miền Nam (SOFRI) & Trung tâm Khuyến nông Quốc gia",
        "summary_vi": "Cây ăn quả nhiệt đới chủ lực (Xoài Cát Hòa Lộc, Cát Chu, Đài Loan, Keo), có thể điều khiển ra hoa rải vụ quanh năm; cần bảo vệ chùm bông khỏi rầy bông xoài, bệnh thán thư và bao trái phòng sâu đục quả.",
        "summary_en": "Major tropical fruit crop (Cat Hoa Loc, Cat Chu, Taiwan) amenable to off-season floral induction; requires strict panicle protection from mango hoppers and anthracnose, plus fruit bagging against borers.",
        "stages": [
            {
                "stage_number": 1,
                "title_vi": "Giai đoạn 1: Cắt tỉa tạo tán sau thu hoạch & Nuôi 2 cơi đọt khỏe",
                "title_en": "Stage 1: Post-Harvest Canopy Pruning & Growing 2 Vigorous Flushes",
                "timing_vi": "0 – 90 ngày sau thu hoạch",
                "timing_en": "0 – 90 days post-harvest",
                "care_vi": "Cắt tỉa cành mang cuống quả, cành vượt bên trong tán, mở cửa sổ tán hình lòng chảo giúp ánh sáng chiếu đều. Bón 20–30kg phân hữu cơ hoai + NPK giàu Đạm - Lân (20-20-15) để thúc 2 cơi đọt ra đồng loạt.",
                "care_en": "Prune spent fruiting shoots and open center canopy windows for sunlight penetration. Apply 20–30kg compost + NPK (20-20-15) to stimulate 2 synchronized vegetative flushes.",
                "notes_vi": "Phun phòng nấm Thán thư và Rầy bông xoài ngay khi cơi đọt non vừa nhú mũi giáo để lá mới không bị cháy đen hoặc cong queo.",
                "notes_en": "Protect emerging spear flushes against anthracnose and mango hoppers so young leaves expand cleanly.",
                "common_diseases": [
                    "Bệnh thán thư hại xoài (Khô bông, đốm đen lá và quả)",
                    "Rầy bông xoài (Rầy chổng cánh xoài)"
                ]
            },
            {
                "stage_number": 2,
                "title_vi": "Giai đoạn 2: Xử lý phân hóa mầm hoa & Kích thích nhú cựa gà",
                "title_en": "Stage 2: Floral Induction & 'Cock-Spur' Bud Break",
                "timing_vi": "Khi cơi đọt thứ 2 đạt 45–60 ngày tuổi (lá lụa già)",
                "timing_en": "When 2nd flush reaches 45–60 days (mature brittle leaves)",
                "care_vi": "Ngưng tưới nước và bón phân Lân - Kali cao (MKP 0-52-34) giúp bộ lá già thuần thục nhanh. Với xử lý rải vụ có thể kết hợp tưới gốc Paclobutrazol đúng liều khuyến cáo. Sau 45–60 ngày khi đỉnh sinh trưởng nhú cựa gà, phun KNO3 (1.5–2%) hoặc Thiourea (0.3–0.5%) kích thích ra bông đồng loạt.",
                "care_en": "Withhold water and spray MKP (0-52-34) to mature foliage (optionally applying regulated Paclobutrazol for off-season crops). At 45–60 days when terminal buds swell, spray KNO3 (1.5–2%) to trigger uniform panicle emergence.",
                "notes_vi": "Rầy bông xoài thường ẩn nấp dưới vỏ thân già và di chuyển lên đẻ trứng ngay khi chồi hoa vừa nhú dài 2–5cm.",
                "notes_en": "Mango hoppers hiding on rough bark migrate to lay eggs into tender flower spikes as soon as buds reach 2–5cm.",
                "common_diseases": [
                    "Rầy bông xoài (Rầy chổng cánh xoài)",
                    "Bệnh thán thư hại xoài (Khô bông, đốm đen lá và quả)"
                ]
            },
            {
                "stage_number": 3,
                "title_vi": "Giai đoạn 3: Vươn phát hoa (Chùm bông) – Nở hoa & Đậu trái non",
                "title_en": "Stage 3: Panicle Elongation, Blooming & Fruit Set",
                "timing_vi": "Kéo dài 25 – 35 ngày từ lúc nhú bông đến đậu trái bằng hạt đậu",
                "timing_en": "25 – 35 days from panicle emergence to pea-sized fruit",
                "care_vi": "Tưới nước giữ ẩm nhẹ đều đặn. Bổ sung Bo và Canxi khi chùm bông dài 10–15cm (trước khi hoa nở) để tăng sức sống hạt phấn và giảm rụng trái non sinh lý. Nếu gặp mưa đêm lúc hoa nở, sáng sớm nên rung nhẹ cành hoặc phun nước rửa bông.",
                "care_en": "Maintain light, even soil moisture. Spray Boron and Calcium when panicles reach 10–15cm (pre-bloom) to boost pollen viability. After night rains during bloom, gently shake branches in early morning to shed water.",
                "notes_vi": "Đây là giai đoạn tối quan trọng: Rầy bông xoài tiết mật ngọt kéo nấm bồ hóng kết hợp nấm Thán thư làm khô đen rụng cả chùm bông ('cháy bông xoài').",
                "notes_en": "Critical stage: Mango hopper honeydew + sooty mold and Colletotrichum anthracnose can blacken and destroy entire blossom panicles.",
                "common_diseases": [
                    "Bệnh thán thư hại xoài (Khô bông, đốm đen lá và quả)",
                    "Rầy bông xoài (Rầy chổng cánh xoài)"
                ]
            },
            {
                "stage_number": 4,
                "title_vi": "Giai đoạn 4: Tỉa trái, Bao trái thương phẩm & Nuôi trái lớn",
                "title_en": "Stage 4: Fruit Thinning, Protective Bagging & Fruit Expansion",
                "timing_vi": "35 – 80 ngày sau đậu trái",
                "timing_en": "35 – 80 days after fruit set",
                "care_vi": "Khi trái qua giai đoạn rụng sinh lý (35–45 ngày sau đậu trái, kích thước bằng ngón chân cái – quả trứng gà), tỉa bỏ trái dị dạng chỉ giữ 1–2 trái đẹp/chùm. Phun phòng nấm và sâu một lượt, đợi khô rồi tiến hành BAO TRÁI bằng túi giấy 2 lớp (vàng hoặc trắng tùy giống). Bón NPK cân đối và tăng Kali ở giai đoạn cuối.",
                "care_en": "After physiological drop (35–45 days post-set, egg-sized fruit), thin to 1–2 uniform fruits/panicle, apply a clean-up fungicide/insecticide spray, let dry, and BAG FRUITS with double-layer paper bags. Apply balanced NPK shifting to high K.",
                "notes_vi": "Bao trái ở 35–45 ngày tuổi là biện pháp hiệu quả nhất để ngăn 100% Sâu đục quả xoài, ruồi đục quả và giảm vết đốm đen thán thư trên vỏ.",
                "notes_en": "Bagging at 35–45 days after fruit set blocks 100% of mango fruit borers/fruit flies and prevents anthracnose tear-stain blemishes.",
                "common_diseases": [
                    "Sâu đục quả xoài (Sâu đục hạt xoài)",
                    "Bệnh thán thư hại xoài (Khô bông, đốm đen lá và quả)"
                ]
            },
            {
                "stage_number": 5,
                "title_vi": "Giai đoạn 5: Thu hoạch đúng độ già & Xử lý sau thu hoạch",
                "title_en": "Stage 5: Maturity Harvest & Post-Harvest Handling",
                "timing_vi": "85 – 110 ngày sau đậu trái",
                "timing_en": "85 – 110 days after fruit set",
                "care_vi": "Thu hoạch khi vai quả nở đầy, phần cuống lõm xuống và phấn trắng phủ đều trên vỏ. Cắt cuống dài 2–5cm và úp ngược quả trên giàn lưới cho chảy hết mủ trong 2–4 giờ để mủ không làm cháy bỏng vỏ xoài.",
                "care_en": "Harvest when fruit shoulders fill out above the stem insertion and natural bloom covers the peel. Clip stems 2–5cm long and invert fruits on racks for 2–4 hours to drain sap and prevent sapburn.",
                "notes_vi": "Nấm thán thư tiềm ẩn ngoài đồng sẽ phát triển mạnh khi xoài chín; với xoài xuất khẩu cần xử lý nước nóng (52°C trong 5 phút) để diệt nấm tiềm ẩn.",
                "notes_en": "Latent field anthracnose erupts during ripening; export mangoes should undergo hot-water treatment (52°C for 5 minutes) after desapping.",
                "common_diseases": [
                    "Bệnh thán thư hại xoài (Khô bông, đốm đen lá và quả)",
                    "Sâu đục quả xoài (Sâu đục hạt xoài)"
                ]
            }
        ]
    },
    {
        "crop": "Thanh long",
        "scientific_name": "Hylocereus undatus / Hylocereus polyrhizus",
        "source_agency": "Viện Cây ăn quả miền Nam (SOFRI) & Sở NN&PTNT Bình Thuận / Long An",
        "summary_vi": "Cây ăn quả họ Xương rồng có bộ rễ ăn nông háo khí, cần trụ leo vững chắc, tủ gốc giữ ẩm bằng rơm rạ kết hợp Trichoderma và phòng trừ nghiêm ngặt bệnh đốm nâu (tắc kè) trong mùa mưa.",
        "summary_en": "Climbing cactus fruit crop with shallow aerobic roots; requires sturdy concrete/living posts, straw mulching with Trichoderma, and strict sanitation against stem canker ('tắc kè') in the rainy season.",
        "stages": [
            {
                "stage_number": 1,
                "title_vi": "Giai đoạn 1: Dựng trụ, Lên mô & Trồng hom giống sạch bệnh",
                "title_en": "Stage 1: Post Installation, Mound Prep & Planting Healthy Cuttings",
                "timing_vi": "Tháng 10–11 hoặc Đầu mùa mưa (Kiến thiết năm đầu)",
                "timing_en": "Oct–Nov or Early rainy season (Establishment year)",
                "care_vi": "Dựng trụ bê tông cao 1.8–2.0m (chôn sâu 0.5m), khoảng cách 2.5x3.0m (1.100–1.300 trụ/ha). Đắp mô cao 20–30cm quanh trụ, bón lót 10–15kg phân chuồng hoai + Trichoderma + 0.5kg lân. Chọn 4 hom giống bánh tẻ (dài 40–50cm, sạch hoàn toàn vết bệnh đốm nâu) đặt sát 4 mặt trụ, buộc dây cố định.",
                "care_en": "Erect 1.8–2.0m concrete posts at 2.5x3.0m spacing. Build 20–30cm mounds with 10–15kg Trichoderma manure + 0.5kg P. Plant 4 mature, canker-free 40–50cm cuttings flat against the 4 sides of each post.",
                "notes_vi": "Chỉ cắm hom sâu 3–5cm trên mặt mô rồi tủ rơm nhẹ; nếu cắm sâu dưới đất ẩm hom sẽ bị thối gốc.",
                "notes_en": "Set cutting bases only 3–5cm deep and mulch lightly with straw; deep burial causes basal stem rot.",
                "common_diseases": [
                    "Bệnh đốm nâu thanh long (Bệnh tắc kè / Đốm trắng)"
                ]
            },
            {
                "stage_number": 2,
                "title_vi": "Giai đoạn 2: Tỉa cành tạo tán hình dù & Nuôi cành mẹ tích lũy nhựa",
                "title_en": "Stage 2: Umbrella Canopy Training & Maturing Cladodes",
                "timing_vi": "Sau mỗi lứa thu hoạch & Giữa các đợt làm bông",
                "timing_en": "Between fruiting cycles",
                "care_vi": "Khi cành vươn lên đỉnh trụ, bấm ngọn để phát sinh các cành cấp 1, cấp 2 buông rủ đều 4 phía như tán dù (giữ khoảng 120–150 cành khỏe/trụ trưởng thành). Tỉa bỏ cành già đã cho trái nhiều lần, cành khuất trong tán và cành bị đốm nâu. Bón phân hữu cơ + NPK giàu Đạm - Lân (20-20-15).",
                "care_en": "Top shoots at the post crown to form a balanced umbrella canopy of 120–150 vigorous cladodes per mature post. Prune spent interior and diseased cladodes, then apply organic manure + NPK (20-20-15).",
                "notes_vi": "Giai đoạn cành non đang vươn dài có lớp biểu bì rất mỏng, cực kỳ mẫn cảm với nấm Neoscytalidium gây đốm trắng lõm (mắt cua/tắc kè).",
                "notes_en": "Young elongating cladodes have tender cuticles and are hyper-susceptible to Neoscytalidium white-sunken spot infection.",
                "common_diseases": [
                    "Bệnh đốm nâu thanh long (Bệnh tắc kè / Đốm trắng)"
                ]
            },
            {
                "stage_number": 3,
                "title_vi": "Giai đoạn 3: Xử lý chong đèn (Rải vụ) hoặc Phân hóa mầm hoa chính vụ",
                "title_en": "Stage 3: Night-Break LED Lighting (Off-Season) or Natural Bud Induction",
                "timing_vi": "Tháng 9 – Tháng 3 năm sau (Vụ chong đèn) / Tháng 4–8 (Chính vụ)",
                "timing_en": "Sep–Mar (Lighting off-season) / Apr–Aug (Natural main season)",
                "care_vi": "Khi cành đã già thuần thục (xanh đậm), bón phân Lân và Kali cao trước khi kéo đèn 7–10 ngày. Chong đèn LED chuyên dụng (8–9W) từ 18h–22h30 hoặc 21h–3h sáng liên tục 15–20 đêm để phá quang chu kỳ ngày ngắn, kích thích cây nhú nụ bông.",
                "care_en": "Once cladodes harden, apply high P-K fertilizer 7–10 days before lighting. Run 8–9W horticulture LED lamps for 15–20 nights to break short-day dormancy and induce flower buds.",
                "notes_vi": "Không chong đèn trên những trụ đang bị bệnh đốm nâu nặng hoặc bộ rễ bị suy kiệt.",
                "notes_en": "Never force-light posts suffering from severe stem canker or root exhaustion.",
                "common_diseases": [
                    "Bệnh đốm nâu thanh long (Bệnh tắc kè / Đốm trắng)"
                ]
            },
            {
                "stage_number": 4,
                "title_vi": "Giai đoạn 4: Tỉa nụ, Nở hoa, Rút râu & Nuôi trái lớn (0–25 ngày sau nở)",
                "title_en": "Stage 4: Bud Thinning, Anthesis, Shuck Removal & Fruit Bulking",
                "timing_vi": "Từ lúc nhú nụ đến 25 ngày sau khi hoa nở",
                "timing_en": "From bud emergence to 25 days after anthesis",
                "care_vi": "Tỉa nụ khi nụ dài 3–5cm, chỉ giữ 1–2 nụ khỏe/cành (khoảng 25–35 nụ/trụ). Sau khi hoa nở 3–4 ngày, tiến hành 'rút râu' (bẻ bỏ phần cánh hoa héo còn dính ở đầu trái) để nước mưa không đọng lại gây thối đầu trái. Bón NPK cân đối và tăng Kali (12-12-17+TE) kết hợp tưới giữ ẩm đều.",
                "care_en": "Thin flower buds at 3–5cm length to 1–2 buds/cladode (25–35 buds/post). 3–4 days post-anthesis, manually remove withered floral perianths ('rút râu') so rainwater does not rot the fruit apex. Fertigate balanced NPK shifting to high K.",
                "notes_vi": "Nụ hoa và trái non là bộ phận dễ nhiễm bệnh đốm nâu nhất; tuyệt đối không vứt cành bệnh, nụ tỉa xuống mặt liếp hay mương nước.",
                "notes_en": "Flower buds and young fruits are prime targets for stem/fruit canker; never drop pruned diseased buds or cladodes onto beds or irrigation canals.",
                "common_diseases": [
                    "Bệnh đốm nâu thanh long (Bệnh tắc kè / Đốm trắng)"
                ]
            },
            {
                "stage_number": 5,
                "title_vi": "Giai đoạn 5: Vuốt tai xanh, Thu hoạch trái chín & Vệ sinh vườn",
                "title_en": "Stage 5: Bract Conditioning, Ripe Harvest & Orchard Sanitation",
                "timing_vi": "28 – 32 ngày sau khi hoa nở",
                "timing_en": "28 – 32 days after anthesis",
                "care_vi": "Vuốt dưỡng chất giữ tai quả xanh cứng đẹp theo tiêu chuẩn VietGAP. Thu hoạch sau khi hoa nở 28–32 ngày (khi vỏ quả chuyển màu đỏ hồng bóng đều), dùng kéo sắc cắt sát ngạnh cành chữ V.",
                "care_en": "Condition fruit bracts under VietGAP guidelines. Harvest at 28–32 days after anthesis using sanitized shears with a neat V-cut at the cladode attachment.",
                "notes_vi": "Rửa kéo cắt bằng cồn/nước vôi và thu gom toàn bộ cành/quả bị đốm nâu đưa vào hố ủ vôi tập trung xa vườn.",
                "notes_en": "Sanitize harvesting shears and bury all canker-infected cladodes/fruits with quicklime in a sealed pit away from the orchard.",
                "common_diseases": [
                    "Bệnh đốm nâu thanh long (Bệnh tắc kè / Đốm trắng)"
                ]
            }
        ]
    },
    {
        "crop": "Rau màu/Bắp cải",
        "scientific_name": "Brassica oleracea / Cruciferae",
        "source_agency": "Viện Nghiên cứu Rau quả (FAVRI) & Cục Bảo vệ thực vật (Chương trình IPM Rau)",
        "summary_vi": "Nhóm rau họ thập tự chủ lực (Bắp cải, Súp lơ, Cải xanh, Cải thảo) ưa khí hậu mát (15–22°C), cần luân canh với lúa nước hoặc cây khác họ và quản lý tổng hợp IPM đối với Sâu tơ, Sâu khoang, Bệnh thối nhũn.",
        "summary_en": "Cruciferous vegetable crops (cabbage, cauliflower, mustard greens) thriving at 15–22°C; require rotation with paddy rice and strict IPM against diamondback moth, armyworms, and bacterial soft rot.",
        "stages": [
            {
                "stage_number": 1,
                "title_vi": "Giai đoạn 1: Ươm cây con trong nhà lưới, Làm đất bón vôi & Trồng",
                "title_en": "Stage 1: Screenhouse Nursery, Soil Liming & Transplanting",
                "timing_vi": "Ươm 20–25 ngày & 0–7 ngày sau trồng",
                "timing_en": "20–25 days nursery & 0–7 days after transplanting (DAT)",
                "care_vi": "Ươm cây con trong khay bầu dưới vòm lưới chắn côn trùng. Đất trồng phải cày bừa kỹ, bón vôi 800–1.000kg/ha phơi ải 10–15 ngày để diệt vi khuẩn thối nhũn. Lên luống cao 20–25cm thoát nước tốt, bón lót 15–20 tấn phân hữu cơ vi sinh + 100% Lân + 20% Đạm.",
                "care_en": "Raise seedlings under insect-proof net tunnels. Incorporate 800–1,000kg/ha lime 10–15 days prior to solarize/sanitize soil against soft-rot bacteria. Form 20–25cm raised beds with 15–20t bio-compost + 100% P + 20% N.",
                "notes_vi": "Không trồng liên tiếp nhiều vụ rau họ thập tự trên cùng một chân đất (nên luân canh với lúa nước, ngô hoặc cây họ đậu).",
                "notes_en": "Never grow successive crucifer crops on the same plot; rotate with paddy rice, corn, or legumes.",
                "common_diseases": [
                    "Sâu tơ hại rau họ thập tự (Bắp cải, Súp lơ, Cải xanh)",
                    "Sâu khoang và Sâu xanh da láng hại rau màu"
                ]
            },
            {
                "stage_number": 2,
                "title_vi": "Giai đoạn 2: Hồi xanh – Phát triển bộ lá ngoài (Trải lá bàng: 7–25 ngày)",
                "title_en": "Stage 2: Recovery & Rosette Leaf Expansion (7–25 DAT)",
                "timing_vi": "7 – 25 ngày sau trồng",
                "timing_en": "7 – 25 days after transplanting",
                "care_vi": "Tưới đủ ẩm ngày 1–2 lần giúp cây bén rễ hồi xanh nhanh. Bón thúc lần 1 (30% Đạm + 20% Kali) lúc 10–12 ngày sau trồng và lần 2 (30% Đạm + 30% Kali) lúc 20–25 ngày kết hợp xới cỏ, vun gốc nhẹ.",
                "care_en": "Irrigate 1–2 times daily for rapid root establishment. Apply 1st top-dressing (30% N + 20% K) at 10–12 DAT and 2nd top-dressing (30% N + 30% K) at 20–25 DAT with light cultivation.",
                "notes_vi": "Đặt bẫy bả chua ngọt và bẫy Pheromone để bắt bướm Sâu khoang, Sâu xanh da láng và Sâu tơ; ngắt bỏ các ổ trứng sâu khoang ở mặt dưới lá.",
                "notes_en": "Deploy sweet-sour bait traps and pheromone traps against adult moths; hand-remove clustered Spodoptera egg masses from leaf undersides.",
                "common_diseases": [
                    "Sâu tơ hại rau họ thập tự (Bắp cải, Súp lơ, Cải xanh)",
                    "Sâu khoang và Sâu xanh da láng hại rau màu"
                ]
            },
            {
                "stage_number": 3,
                "title_vi": "Giai đoạn 3: Bắt đầu cuốn bắp / Hình thành hoa súp lơ (25–45 ngày)",
                "title_en": "Stage 3: Cupping / Early Head & Curd Initiation (25–45 DAT)",
                "timing_vi": "25 – 45 ngày sau trồng",
                "timing_en": "25 – 45 days after transplanting",
                "care_vi": "Giai đoạn cây cần nhiều dinh dưỡng nhất để khép lá nõn cuốn bắp. Bón thúc lần 3 (20% Đạm + 50% Kali còn lại) kết hợp bổ sung Canxi-Bo qua lá giúp vách tế bào lá cứng chắc.",
                "care_en": "Peak nutrient demand as inner leaves cup to form heads. Apply final top-dressing (20% N + 50% K) and foliar Ca-B to strengthen cell walls.",
                "notes_vi": "Phải kiểm soát triệt để Sâu tơ và Sâu khoang TRƯỚC khi bắp cải cuốn chặt (vì khi sâu đã chui vào trong bắp sẽ không phun thuốc tới được và vết phân sâu là cửa ngõ cho vi khuẩn thối nhũn xâm nhập).",
                "notes_en": "Control diamondback moth and armyworms BEFORE heads close tightly (once larvae bore inside the head, sprays cannot reach them and feeding wounds trigger bacterial soft rot).",
                "common_diseases": [
                    "Sâu tơ hại rau họ thập tự (Bắp cải, Súp lơ, Cải xanh)",
                    "Sâu khoang và Sâu xanh da láng hại rau màu",
                    "Bệnh thối nhũn vi khuẩn hại bắp cải và rau màu"
                ]
            },
            {
                "stage_number": 4,
                "title_vi": "Giai đoạn 4: Vào chắc bắp / Phát triển hoa thương phẩm (45–65 ngày)",
                "title_en": "Stage 4: Head Firming / Curd Enlargement (45–65 DAT)",
                "timing_vi": "45 – 65 ngày sau trồng",
                "timing_en": "45 – 65 days after transplanting",
                "care_vi": "Tưới nước vào rãnh hoặc tưới gốc nhẹ nhàng, không tưới phun mưa mạnh từ trên đỉnh vào buổi chiều tối để tránh nước đọng trong nõn bắp qua đêm. Tuyệt đối ngừng bón phân đạm.",
                "care_en": "Use furrow or drip irrigation; avoid heavy evening overhead sprinkling that leaves standing water on heads overnight. Stop all nitrogen applications.",
                "notes_vi": "Nếu phát hiện cây bị thối nhũn có mùi hôi thối đặc trưng, phải nhổ bỏ nhẹ nhàng cho vào túi nilon đem tiêu hủy và rắc vôi bột trực tiếp vào hốc đất vừa nhổ.",
                "notes_en": "Immediately bag and remove any plant showing foul-smelling bacterial soft rot, and apply quicklime directly to the planting hole.",
                "common_diseases": [
                    "Bệnh thối nhũn vi khuẩn hại bắp cải và rau màu",
                    "Sâu tơ hại rau họ thập tự (Bắp cải, Súp lơ, Cải xanh)",
                    "Sâu khoang và Sâu xanh da láng hại rau màu"
                ]
            },
            {
                "stage_number": 5,
                "title_vi": "Giai đoạn 5: Thu hoạch an toàn VietGAP & Vệ sinh đồng ruộng",
                "title_en": "Stage 5: VietGAP Safe Harvest & Post-Harvest Sanitation (65–80 DAT)",
                "timing_vi": "65 – 80 ngày sau trồng (Bắp cải) / 30–35 ngày (Rau cải ăn lá)",
                "timing_en": "65 – 80 DAT (Cabbage) / 30–35 DAT (Leafy greens)",
                "care_vi": "Thu hoạch khi bắp cuốn chặt cứng vào sáng sớm hoặc chiều mát; giữ lại 2–3 lá xanh ngoài cùng để bảo vệ bắp khi vận chuyển. Không thu hoạch lúc trời đang mưa hoặc bắp còn ướt sương.",
                "care_en": "Harvest firm heads in cool dry hours, retaining 2–3 wrapper leaves for transport protection. Never harvest in rain or heavy dew.",
                "notes_vi": "Tuân thủ nghiêm ngặt thời gian cách ly (PHI) của thuốc BVTV. Dọn sạch toàn bộ gốc và lá già trên ruộng sau thu hoạch đem ủ vôi.",
                "notes_en": "Strictly respect Pre-Harvest Intervals (PHI). Clear all crop residues and old leaves from the field immediately after harvest.",
                "common_diseases": [
                    "Bệnh thối nhũn vi khuẩn hại bắp cải và rau màu"
                ]
            }
        ]
    },
    {
        "crop": "Lạc/Đậu tương",
        "scientific_name": "Arachis hypogaea / Glycine max",
        "source_agency": "Viện Khoa học Nông nghiệp Việt Nam (VAAS) & Viện Cây lương thực và Cây thực phẩm",
        "summary_vi": "Nhóm cây họ Đậu cố định đạm sinh học cải tạo đất rất tốt; cần đất cát pha/thịt nhẹ tơi xốp, bổ sung đầy đủ Vôi (Canxi) và Lân để củ lạc/quả đậu chắc hạt, phòng bệnh đốm lá và gỉ sắt.",
        "summary_en": "Nitrogen-fixing leguminous oilseed/protein crops requiring loose sandy loam, abundant Calcium (lime) and Phosphorus for pod filling, and foliar protection against leaf spots and rust.",
        "stages": [
            {
                "stage_number": 1,
                "title_vi": "Giai đoạn 1: Làm đất tơi xốp, Bón lót Vôi – Lân & Gieo hạt (0–10 ngày)",
                "title_en": "Stage 1: Loose Bed Prep, Lime–Phosphorus Basal & Sowing (0–10 DAS)",
                "timing_vi": "0 – 10 ngày sau gieo (Vụ Xuân T2–T3 hoặc Vụ Thu Đông T8–T9)",
                "timing_en": "0 – 10 days after sowing (Spring Feb–Mar or Autumn Aug–Sep)",
                "care_vi": "Cày bừa nhỏ đất, lên luống rộng 1.0–1.2m cao 20–25cm. Bón lót 8–10 tấn phân chuồng hoai + 400–500kg Lân supe + 50% lượng Vôi bột (250kg/ha) + chế phẩm vi khuẩn nốt sần Rhizobium. Với lạc vụ Xuân nên áp dụng kỹ thuật che phủ nilon giúp giữ ấm, giữ ẩm và tăng năng suất 20–30%.",
                "care_en": "Prepare fine, loose 20–25cm beds. Apply 8–10t compost + 400–500kg superphosphate + 250kg lime/ha + Rhizobium inoculant. Use polyethylene mulch for Spring peanut to boost soil warmth and yield by 20–30%.",
                "notes_vi": "Chọn hạt giống từ ruộng sạch bệnh, phơi khô giòn vỏ lụa trước khi bóc (lạc) và xử lý thuốc nấm trước khi gieo.",
                "notes_en": "Use certified disease-free seed, sun-dry peanut pods before shelling, and treat seeds prior to sowing.",
                "common_diseases": [
                    "Bệnh đốm nâu và đốm đen hại lạc (Đậu phộng)",
                    "Bệnh sương mai và gỉ sắt hại đậu tương (Đậu nành)"
                ]
            },
            {
                "stage_number": 2,
                "title_vi": "Giai đoạn 2: Cây con 2–5 lá thật & Hình thành nốt sần (10–25 ngày)",
                "title_en": "Stage 2: V2–V5 Seedling & Root Nodulation (10–25 DAS)",
                "timing_vi": "10 – 25 ngày sau gieo",
                "timing_en": "10 – 25 days after sowing",
                "care_vi": "Khi cây có 2–3 lá thật, tiến hành dặm tỉa, xới cỏ phá váng lần 1 và bón thúc nhẹ (một lượng nhỏ Đạm khởi động 30–40kg Urea/ha + Kali) giúp cây phát triển thân lá ban đầu trước khi nốt sần tự cố định đạm.",
                "care_en": "At 2–3 true leaves, thin seedlings, cultivate lightly to break soil crust, and apply a small starter N + K dose before root nodules begin active N-fixation.",
                "notes_vi": "Lạc không che phủ nilon khi xới lần 1 nên 'xới xả' (gạt nhẹ đất quanh gốc để lộ cổ thân cho cặp cành cấp 1 phát triển khỏe).",
                "notes_en": "On unmulched peanuts, gently pull soil away from the cotyledonary node at first weeding to invigorate primary lateral branches.",
                "common_diseases": [
                    "Bệnh đốm nâu và đốm đen hại lạc (Đậu phộng)",
                    "Bệnh sương mai và gỉ sắt hại đậu tương (Đậu nành)"
                ]
            },
            {
                "stage_number": 3,
                "title_vi": "Giai đoạn 3: Ra hoa rộ – Đâm tia củ (Lạc) / Đậu quả non (Đậu tương)",
                "title_en": "Stage 3: Full Bloom – Pegging (Peanut) / Pod Set (Soybean) (25–50 DAS)",
                "timing_vi": "25 – 50 ngày sau gieo",
                "timing_en": "25 – 50 days after sowing",
                "care_vi": "Khi lạc bắt đầu ra hoa rộ và đâm tia (35–40 NSS), tiến hành bón 50% lượng Vôi bột còn lại (250–300kg/ha) rắc đều quanh gốc kết hợp vun gốc (với lạc không phủ nilon) để tia củ đâm xuống đất thuận lợi. Với đậu tương: phun bổ sung Bo và Mo lúc bắt đầu ra hoa.",
                "care_en": "At peak flowering and pegging (35–40 DAS), side-dress the remaining 250–300kg/ha agricultural lime around peanut plants and hill soil so pegs penetrate easily. On soybean, spray foliar Boron and Molybdenum at R1–R2 bloom.",
                "notes_vi": "Canxi (Vôi) được tia củ lạc hấp thụ trực tiếp từ lớp đất mặt 5–10cm; nếu thiếu vôi ở giai đoạn đâm tia, củ lạc sẽ bị lép hoặc thối nhân.",
                "notes_en": "Peanut pegs absorb Calcium directly from the top 5–10cm pegging zone; Ca deficiency during pegging causes empty 'pops' and dark plumule disorder.",
                "common_diseases": [
                    "Bệnh đốm nâu và đốm đen hại lạc (Đậu phộng)",
                    "Bệnh sương mai và gỉ sắt hại đậu tương (Đậu nành)"
                ]
            },
            {
                "stage_number": 4,
                "title_vi": "Giai đoạn 4: Phát triển củ / Vào chắc hạt (50–80 ngày sau gieo)",
                "title_en": "Stage 4: Pod Filling & Seed Enlargement (50–80 DAS)",
                "timing_vi": "50 – 80 ngày sau gieo",
                "timing_en": "50 – 80 days after sowing",
                "care_vi": "Duy trì độ ẩm đất 70–75% và phun phân bón lá giàu Lân - Kali giúp vận chuyển chất khô về hạt. Kiểm tra các lá tầng dưới để phòng trừ sớm bệnh đốm nâu, đốm đen hại lạc và bệnh gỉ sắt, sương mai hại đậu tương.",
                "care_en": "Maintain 70–75% soil moisture and spray foliar P-K to maximize seed filling. Scout lower leaves closely to control early/late leaf spot on peanut and rust/downy mildew on soybean.",
                "notes_vi": "Nếu để bệnh đốm đen hoặc gỉ sắt làm rụng lá sớm ở giai đoạn 55–75 NSS, năng suất hạt sẽ giảm từ 30–50%.",
                "notes_en": "Premature defoliation from late leaf spot or soybean rust during 55–75 DAS cuts pod yield by 30–50%.",
                "common_diseases": [
                    "Bệnh đốm nâu và đốm đen hại lạc (Đậu phộng)",
                    "Bệnh sương mai và gỉ sắt hại đậu tương (Đậu nành)"
                ]
            },
            {
                "stage_number": 5,
                "title_vi": "Giai đoạn 5: Chín sinh lý, Thu hoạch & Phơi bảo quản (80–105 ngày)",
                "title_en": "Stage 5: Physiological Maturity, Harvest & Drying (80–105 DAS)",
                "timing_vi": "80 – 105 ngày sau gieo",
                "timing_en": "80 – 105 days after sowing",
                "care_vi": "Thu hoạch lạc khi 75–80% số củ đã già (gân vỏ củ nổi rõ, mặt trong vỏ củ chuyển màu nâu đen, vỏ lụa hạt căng hồng). Thu hoạch đậu tương khi lá rụng hết và >85% quả trên cây chuyển màu nâu vàng khô.",
                "care_en": "Harvest peanuts when 75–80% of pods show prominent hull netting, dark inner pericarp, and pink testa. Harvest soybeans when leaves drop and >85% of pods turn brown.",
                "notes_vi": "Phơi khô củ lạc ngay sau khi nhổ xuống độ ẩm <9–10% để ngăn ngừa nấm Aspergillus flavus tiết độc tố Aflatoxin. Thân lá sạch bệnh có thể ủ làm phân xanh cải tạo đất.",
                "notes_en": "Dry harvested peanut pods immediately to <9–10% moisture to prevent Aspergillus flavus aflatoxin contamination.",
                "common_diseases": [
                    "Bệnh đốm nâu và đốm đen hại lạc (Đậu phộng)",
                    "Bệnh sương mai và gỉ sắt hại đậu tương (Đậu nành)"
                ]
            }
        ]
    }
]


def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    diseases_path = os.path.join(root_dir, "app", "data", "vn_diseases.json")
    out_path = os.path.join(root_dir, "app", "data", "vn_crop_guides.json")

    with open(diseases_path, "r", encoding="utf-8") as f:
        diseases = json.load(f)

    valid_names = {d["name_vi"] for d in diseases}
    valid_crops = {d["crop"] for d in diseases}

    assert len(GUIDES) == 15, f"Expected 15 crop guides, got {len(GUIDES)}"
    for g in GUIDES:
        assert g["crop"] in valid_crops, f"Unknown crop: {g['crop']}"
        assert len(g["stages"]) == 5, f"Crop {g['crop']} does not have 5 stages"
        for st in g["stages"]:
            for dname in st["common_diseases"]:
                assert dname in valid_names, f"Disease '{dname}' in {g['crop']} stage {st['stage_number']} not in vn_diseases.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(GUIDES, f, ensure_ascii=False, indent=2)

    print(f"Successfully wrote {len(GUIDES)} crop guides (75 stages total) to {out_path}")


if __name__ == "__main__":
    main()

