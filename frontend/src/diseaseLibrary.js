export const diseaseLibrary = [
  {
    crop: { vi: '🌾 Lúa', en: '🌾 Rice' },
    diseases: [
      {
        name: { vi: 'Bạc lá (Bacterial Blight)', en: 'Bacterial Blight' },
        scientific: 'Xanthomonas oryzae pv. oryzae',
        severity: 'high',
        image: 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/Bacterial_leaf_blight_of_paddy.jpg/320px-Bacterial_leaf_blight_of_paddy.jpg',
        symptoms: {
          vi: 'Lá cháy từ mép và đầu lá vào trong, chuyển màu trắng xám. Vết bệnh có thể dài 20-30cm. Khi ẩm, mép vết bệnh có giọt dịch vi khuẩn màu vàng.',
          en: 'Leaves turn white-gray from edges and tips inward. Lesions can be 20-30cm long. In humid conditions, yellow bacterial ooze appears at lesion margins.'
        },
        conditions: {
          vi: 'Phát triển mạnh khi mưa nhiều, gió lớn, bón thừa đạm, mật độ gieo dày.',
          en: 'Thrives in rainy, windy conditions with excess nitrogen and dense planting.'
        },
        prevention: {
          vi: ['Sử dụng giống kháng bệnh (IR64, IRBB21)', 'Bón phân cân đối, giảm đạm', 'Không tưới tràn từ ruộng bệnh sang ruộng khỏe', 'Vệ sinh đồng ruộng sau thu hoạch', 'Xử lý hạt giống bằng nước nóng 54°C/10 phút'],
          en: ['Use resistant varieties (IR64, IRBB21)', 'Balanced fertilization, reduce nitrogen', 'Avoid overflow irrigation from infected fields', 'Field sanitation after harvest', 'Hot water seed treatment at 54°C for 10 min']
        },
        treatment: {
          vi: ['Phun Kasugamycin 2% (Kasumin) 1.5-2 lít/ha', 'Phun Bismerthiazol (Xanthomycin) 20WP', 'Đồng oxychloride 30WP khi bệnh nhẹ', 'Ngừng bón đạm, tháo nước ruộng'],
          en: ['Spray Kasugamycin 2% (Kasumin) 1.5-2 L/ha', 'Spray Bismerthiazol (Xanthomycin) 20WP', 'Copper oxychloride 30WP for mild cases', 'Stop nitrogen, drain field water']
        },
      },
      {
        name: { vi: 'Đạo ôn (Blast)', en: 'Rice Blast' },
        scientific: 'Magnaporthe oryzae',
        severity: 'high',
        image: 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/Rice_blast_symptoms.jpg/320px-Rice_blast_symptoms.jpg',
        symptoms: {
          vi: 'Vết đốm hình mắt én (thoi) trên lá, tâm xám trắng, viền nâu. Có thể gây cháy lá, thối cổ bông (đạo ôn cổ bông) làm bông lép trắng.',
          en: 'Diamond/eye-shaped lesions on leaves with gray-white center and brown border. Can cause leaf burn and neck rot (panicle blast) leading to empty white grains.'
        },
        conditions: {
          vi: 'Nhiệt độ 20-28°C, ẩm độ >90%, sương mù nhiều, bón thừa đạm, thiếu ánh sáng.',
          en: 'Temperature 20-28°C, humidity >90%, frequent fog, excess nitrogen, low light.'
        },
        prevention: {
          vi: ['Dùng giống kháng đạo ôn', 'Bón phân cân đối NPK, không thừa đạm', 'Gieo cấy mật độ vừa phải', 'Xử lý hạt giống bằng thuốc trừ nấm', 'Quản lý nước hợp lý (không để ruộng khô hạn)'],
          en: ['Use blast-resistant varieties', 'Balanced NPK fertilization, avoid excess N', 'Moderate planting density', 'Fungicide seed treatment', 'Proper water management (avoid drought stress)']
        },
        treatment: {
          vi: ['Tricyclazole (Beam 75WP) 300g/ha — phòng trị tốt nhất', 'Isoprothiolane (Fuji-one 40EC) 1-1.5 lít/ha', 'Kasugamycin + Tricyclazole hỗn hợp', 'Phun khi lúa trỗ để phòng đạo ôn cổ bông'],
          en: ['Tricyclazole (Beam 75WP) 300g/ha — best preventive', 'Isoprothiolane (Fuji-one 40EC) 1-1.5 L/ha', 'Kasugamycin + Tricyclazole combination', 'Spray at heading stage to prevent panicle blast']
        },
      },
      {
        name: { vi: 'Đốm nâu (Brown Spot)', en: 'Brown Spot' },
        scientific: 'Bipolaris oryzae (Cochliobolus miyabeanus)',
        severity: 'medium',
        image: 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Brown_spot_of_rice.jpg/320px-Brown_spot_of_rice.jpg',
        symptoms: {
          vi: 'Đốm nâu hình oval trên lá, kích thước 1-2cm, tâm xám nhạt viền nâu đậm. Xuất hiện nhiều trên lá già, đất nghèo dinh dưỡng.',
          en: 'Oval brown spots on leaves, 1-2cm, light gray center with dark brown border. Common on older leaves in nutrient-poor soil.'
        },
        conditions: {
          vi: 'Đất thiếu kali, kẽm, silic. Cây suy yếu do ngập úng hoặc hạn. Hạt giống nhiễm bệnh.',
          en: 'Soil deficient in potassium, zinc, silicon. Weakened plants from flooding or drought. Infected seeds.'
        },
        prevention: {
          vi: ['Bón đủ kali (K₂O) và kẽm (ZnSO₄)', 'Bón silic (phân lân nung chảy)', 'Xử lý hạt giống trước khi gieo', 'Không để ruộng khô hạn kéo dài'],
          en: ['Apply sufficient potassium (K₂O) and zinc (ZnSO₄)', 'Apply silicon (fused phosphate)', 'Seed treatment before sowing', 'Avoid prolonged drought']
        },
        treatment: {
          vi: ['Mancozeb 80WP (2-3 kg/ha)', 'Propiconazole (Tilt 250EC) 0.5 lít/ha', 'Iprodione (Rovral 50WP)', 'Carbendazim 50WP khi bệnh nặng'],
          en: ['Mancozeb 80WP (2-3 kg/ha)', 'Propiconazole (Tilt 250EC) 0.5 L/ha', 'Iprodione (Rovral 50WP)', 'Carbendazim 50WP for severe cases']
        },
      },
      {
        name: { vi: 'Vàng lùn (Tungro)', en: 'Tungro' },
        scientific: 'RTSV + RTBV (virus kép)',
        severity: 'high',
        image: 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Rice_tungro_disease.jpg/320px-Rice_tungro_disease.jpg',
        symptoms: {
          vi: 'Lá chuyển vàng cam từ đầu lá xuống, cây lùn còi cọc, đẻ nhánh ít, bông ngắn lép. Lá non có thể có đốm gỉ sắt.',
          en: 'Leaves turn orange-yellow from tips, plants stunted with few tillers, short empty panicles. Young leaves may show rust-colored spots.'
        },
        conditions: {
          vi: 'Lây lan qua rầy xanh (Nephotettix virescens). Bùng phát khi mật độ rầy cao, gieo muộn.',
          en: 'Transmitted by green leafhoppers (Nephotettix virescens). Outbreaks when leafhopper density is high, late planting.'
        },
        prevention: {
          vi: ['Gieo cấy đồng loạt, tránh gieo muộn', 'Dùng giống kháng rầy xanh', 'Nhổ bỏ và tiêu hủy cây bệnh sớm', 'Diệt rầy xanh bằng bẫy đèn', 'Không trồng lúa liên tục quanh năm'],
          en: ['Synchronous planting, avoid late sowing', 'Use leafhopper-resistant varieties', 'Remove and destroy infected plants early', 'Light traps for leafhoppers', 'Avoid continuous rice cropping']
        },
        treatment: {
          vi: ['Không có thuốc trị virus — chỉ phòng bằng diệt rầy', 'Imidacloprid 100SL (diệt rầy xanh)', 'Thiamethoxam 25WG', 'Buprofezin 10WP (ức chế lột xác rầy)'],
          en: ['No cure for virus — prevention by controlling leafhoppers', 'Imidacloprid 100SL (kill leafhoppers)', 'Thiamethoxam 25WG', 'Buprofezin 10WP (inhibit leafhopper molting)']
        },
      },
    ]
  },
  {
    crop: { vi: '🌽 Ngô', en: '🌽 Corn' },
    diseases: [
      {
        name: { vi: 'Rỉ sắt ngô (Common Rust)', en: 'Common Rust' },
        scientific: 'Puccinia sorghi',
        severity: 'medium',
        image: 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Puccinia_sorghi_uredinia.jpg/320px-Puccinia_sorghi_uredinia.jpg',
        symptoms: {
          vi: 'Mụn bột (uredinia) màu nâu đỏ/gỉ sắt nổi trên cả 2 mặt lá. Khi nặng, lá khô cháy sớm, giảm năng suất 10-40%.',
          en: 'Reddish-brown pustules (uredinia) on both leaf surfaces. Severe cases cause premature leaf drying, 10-40% yield loss.'
        },
        conditions: {
          vi: 'Nhiệt độ mát 16-23°C, ẩm độ cao, sương đêm nhiều. Phổ biến vụ đông xuân.',
          en: 'Cool temperatures 16-23°C, high humidity, heavy dew. Common in cool seasons.'
        },
        prevention: {
          vi: ['Trồng giống kháng rỉ sắt', 'Gieo đúng thời vụ tránh mùa mát ẩm', 'Mật độ trồng hợp lý, thông thoáng', 'Vệ sinh tàn dư cây bệnh'],
          en: ['Plant rust-resistant varieties', 'Timely planting to avoid cool humid seasons', 'Proper spacing for ventilation', 'Remove crop residues']
        },
        treatment: {
          vi: ['Propiconazole (Tilt 250EC) 0.5 lít/ha', 'Azoxystrobin (Amistar 250SC)', 'Mancozeb 80WP phun phòng', 'Phun khi thấy mụn đầu tiên, lặp lại sau 7-10 ngày'],
          en: ['Propiconazole (Tilt 250EC) 0.5 L/ha', 'Azoxystrobin (Amistar 250SC)', 'Mancozeb 80WP preventive spray', 'Spray at first pustules, repeat after 7-10 days']
        },
      },
      {
        name: { vi: 'Cháy lá phương Bắc (Northern Leaf Blight)', en: 'Northern Leaf Blight' },
        scientific: 'Exserohilum turcicum',
        severity: 'medium',
        image: 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Exserohilum_turcicum_on_maize.jpg/320px-Exserohilum_turcicum_on_maize.jpg',
        symptoms: {
          vi: 'Vết bệnh dài 5-15cm hình thuyền/xì gà, màu xám xanh rồi chuyển nâu. Bắt đầu từ lá dưới lan lên. Nặng làm lá khô hoàn toàn.',
          en: 'Long cigar-shaped lesions 5-15cm, gray-green turning brown. Starts from lower leaves upward. Severe cases cause complete leaf drying.'
        },
        conditions: {
          vi: 'Nhiệt độ 18-27°C, ẩm độ cao, mưa nhiều. Nấm tồn tại trên tàn dư cây bệnh.',
          en: 'Temperature 18-27°C, high humidity, frequent rain. Fungus survives on crop residues.'
        },
        prevention: {
          vi: ['Luân canh với cây trồng khác (đậu, lúa)', 'Vùi sâu tàn dư ngô sau thu hoạch', 'Giống kháng bệnh (gen Ht1, Ht2)', 'Không trồng ngô liên tục trên cùng đất'],
          en: ['Rotate with other crops (legumes, rice)', 'Deep burial of corn residues after harvest', 'Resistant varieties (Ht1, Ht2 genes)', 'Avoid continuous corn on same land']
        },
        treatment: {
          vi: ['Azoxystrobin + Propiconazole hỗn hợp', 'Mancozeb 80WP (2.5-3 kg/ha)', 'Phun khi bệnh xuất hiện ở lá dưới', 'Phun lặp lại sau 10-14 ngày nếu cần'],
          en: ['Azoxystrobin + Propiconazole combination', 'Mancozeb 80WP (2.5-3 kg/ha)', 'Spray when disease appears on lower leaves', 'Repeat after 10-14 days if needed']
        },
      },
    ]
  },
  {
    crop: { vi: '🍅 Cà chua', en: '🍅 Tomato' },
    diseases: [
      {
        name: { vi: 'Héo muộn (Late Blight)', en: 'Late Blight' },
        scientific: 'Phytophthora infestans',
        severity: 'high',
        image: 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/Phytophthora_infestans-tomato.jpg/320px-Phytophthora_infestans-tomato.jpg',
        symptoms: {
          vi: 'Vết nâu đen ướt lan nhanh trên lá, thân, quả. Mặt dưới lá có lớp mốc trắng khi ẩm. Quả thối nâu cứng. Có thể phá hủy cả ruộng trong 1 tuần.',
          en: 'Wet dark brown spots spread rapidly on leaves, stems, fruits. White mold underneath in humid conditions. Fruits develop firm brown rot. Can destroy entire field in a week.'
        },
        conditions: {
          vi: 'Nhiệt độ mát 15-22°C, ẩm độ >90%, mưa phùn kéo dài. Nguy hiểm nhất vụ đông.',
          en: 'Cool temperatures 15-22°C, humidity >90%, prolonged drizzle. Most dangerous in cool seasons.'
        },
        prevention: {
          vi: ['Trồng giống kháng (có gen Ph-2, Ph-3)', 'Trồng trên luống cao, thoát nước tốt', 'Tỉa lá gốc, thông thoáng', 'Phun phòng Mancozeb trước mùa mưa', 'Không tưới phun vào chiều tối'],
          en: ['Plant resistant varieties (Ph-2, Ph-3 genes)', 'Raised beds with good drainage', 'Prune lower leaves for ventilation', 'Preventive Mancozeb spray before rainy season', 'Avoid overhead irrigation in evening']
        },
        treatment: {
          vi: ['Metalaxyl + Mancozeb (Ridomil Gold 68WG) — đặc trị', 'Dimethomorph (Acrobat MZ)', 'Chlorothalonil (Daconil 75WP)', 'Phun ngay khi phát hiện, lặp lại 5-7 ngày', 'Nhổ bỏ cây bệnh nặng, tiêu hủy'],
          en: ['Metalaxyl + Mancozeb (Ridomil Gold 68WG) — specific treatment', 'Dimethomorph (Acrobat MZ)', 'Chlorothalonil (Daconil 75WP)', 'Spray immediately upon detection, repeat 5-7 days', 'Remove and destroy severely infected plants']
        },
      },
      {
        name: { vi: 'Virus xoăn lá vàng (TYLCV)', en: 'Tomato Yellow Leaf Curl Virus' },
        scientific: 'Begomovirus (TYLCV)',
        severity: 'high',
        image: 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Tomato_yellow_leaf_curl_virus_symptoms.jpg/320px-Tomato_yellow_leaf_curl_virus_symptoms.jpg',
        symptoms: {
          vi: 'Lá non xoăn lên, vàng mép lá, cây còi cọc lùn. Hoa rụng, quả ít và nhỏ. Cây nhiễm sớm có thể không cho thu hoạch.',
          en: 'Young leaves curl upward, yellow leaf margins, stunted plants. Flower drop, few small fruits. Early infection may yield nothing.'
        },
        conditions: {
          vi: 'Lây qua bọ phấn trắng (Bemisia tabaci). Bùng phát mùa khô nóng, mật độ bọ phấn cao.',
          en: 'Transmitted by whiteflies (Bemisia tabaci). Outbreaks in hot dry seasons with high whitefly populations.'
        },
        prevention: {
          vi: ['Lưới chắn côn trùng (mesh 50)', 'Bẫy dính vàng để theo dõi bọ phấn', 'Giống kháng TYLCV (gen Ty-1, Ty-3)', 'Nhổ bỏ cây bệnh ngay khi phát hiện', 'Trồng xen cây xua đuổi (húng quế)'],
          en: ['Insect-proof nets (50 mesh)', 'Yellow sticky traps to monitor whiteflies', 'TYLCV-resistant varieties (Ty-1, Ty-3 genes)', 'Remove infected plants immediately', 'Intercrop with repellent plants (basil)']
        },
        treatment: {
          vi: ['Không có thuốc trị virus — chỉ diệt bọ phấn', 'Imidacloprid 200SL (tưới gốc hoặc phun)', 'Thiamethoxam 25WG', 'Spiromesifen (Oberon 240SC) diệt trứng+ấu trùng', 'Dầu khoáng phun xua đuổi'],
          en: ['No cure for virus — control whiteflies only', 'Imidacloprid 200SL (drench or spray)', 'Thiamethoxam 25WG', 'Spiromesifen (Oberon 240SC) kills eggs+nymphs', 'Mineral oil spray as repellent']
        },
      },
    ]
  },
  {
    crop: { vi: '🥔 Khoai tây', en: '🥔 Potato' },
    diseases: [
      {
        name: { vi: 'Héo muộn (Late Blight)', en: 'Late Blight' },
        scientific: 'Phytophthora infestans',
        severity: 'high',
        image: 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Potato_late_blight.jpg/320px-Potato_late_blight.jpg',
        symptoms: {
          vi: 'Vết nâu đen ướt trên lá, lan rất nhanh khi ẩm. Mặt dưới có mốc trắng. Củ bị thối nâu từ ngoài vào. Mùi hôi khi thối nặng.',
          en: 'Wet dark brown spots on leaves, spread rapidly in humidity. White mold underneath. Tubers develop brown rot from outside in. Foul smell when severely rotted.'
        },
        conditions: {
          vi: 'Nhiệt độ 12-20°C, ẩm >90%, mưa phùn. Nguy hiểm nhất vụ đông xuân ở miền Bắc.',
          en: 'Temperature 12-20°C, humidity >90%, drizzle. Most dangerous in cool seasons.'
        },
        prevention: {
          vi: ['Giống kháng (Solara, Atlantic kháng vừa)', 'Trồng luống cao, thoát nước tốt', 'Dùng củ giống sạch bệnh', 'Phun phòng Mancozeb từ khi cây cao 15-20cm', 'Thu hoạch khi trời khô, phơi củ trước bảo quản'],
          en: ['Resistant varieties (Solara, Atlantic moderate resistance)', 'High ridges with good drainage', 'Use disease-free seed tubers', 'Preventive Mancozeb from 15-20cm plant height', 'Harvest in dry weather, cure tubers before storage']
        },
        treatment: {
          vi: ['Metalaxyl + Mancozeb (Ridomil Gold 68WG)', 'Cymoxanil + Mancozeb (Curzate M8)', 'Dimethomorph 50WP', 'Phun 5-7 ngày/lần khi thời tiết thuận lợi cho bệnh', 'Cắt bỏ thân lá 2 tuần trước thu hoạch'],
          en: ['Metalaxyl + Mancozeb (Ridomil Gold 68WG)', 'Cymoxanil + Mancozeb (Curzate M8)', 'Dimethomorph 50WP', 'Spray every 5-7 days in favorable disease weather', 'Cut haulms 2 weeks before harvest']
        },
      },
    ]
  },
]
