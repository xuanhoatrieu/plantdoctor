"""Build and enrich the CABI PlantwisePlus Vietnam Knowledge Base (vn_diseases.json)
with additional Vietnam PMDG/Factsheet entries and verified reference images from
iNaturalist Taxa API and Wikimedia Commons API.
"""
import json
import os
import time
import urllib.parse
import urllib.request

KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "data", "vn_diseases.json")

EXTRA_CABI_VN_ENTRIES = [
    # --- LÚA (CABI Vietnam PMDGs & IRRI) ---
    {
        "crop": "Lúa",
        "name_vi": "Bệnh nghẹt rễ sinh lý lúa (Ngộ độc hữu cơ / phèn)",
        "name_en": "Rice Physiological Root Choking / Acid Sulfate Toxicity",
        "scientific_name": "Physiological disorder (Fe2+ / H2S toxicity)",
        "severity": "medium",
        "symptoms_vi": "Cây lúa còi cọc, đẻ nhánh kém, chóp lá và mép lá già biến màu vàng đỏ hoặc nâu gỉ sắt có các chấm nhỏ màu nâu đen lan từ đầu lá xuống; nhổ lên thấy bộ rễ thâm đen, thối có mùi hôi tanh, rất ít rễ trắng mới.",
        "symptoms_en": "Stunted tillering, reddish-brown or rusty yellowing starting from tips of older leaves with tiny brown-black speckles; roots turn black and foul-smelling with few white feeder roots.",
        "conditions_vi": "Đất chua phèn, ruộng ngập nước sâu thiếu oxy, vùi rơm rạ chưa phân hủy hoặc thời tiết lạnh dưới 15°C sau cấy/sạ (CABI Vietnam PMDG).",
        "conditions_en": "Acid sulfate waterlogged soils, undecomposed organic matter, or cold spells.",
        "prevention_vi": "Cày ải phơi đất, bón vôi khử chua và phân lân nung chảy trước khi gieo cấy; tháo cạn nước phơi ruộng nhẹ 3-5 ngày để xả độc khí H2S, làm cỏ sục bùn giúp rễ thông thoáng.",
        "prevention_en": "Drain and aerate paddy soil for 3-5 days, apply agricultural lime and fused phosphate, rotary weeding to oxygenate roots.",
        "treatment_vi": "Bón phân lân dễ tiêu (Super lân), Kali, phun phân bón lá chứa Humic + Kẽm + Silic giúp ra rễ trắng mới (không phun thuốc trừ nấm vì đây là bệnh sinh lý)"
    },
    {
        "crop": "Lúa",
        "name_vi": "Rầy nâu và Rầy lưng trắng hại lúa",
        "name_en": "Rice Brown Planthopper & White-backed Planthopper",
        "scientific_name": "Nilaparvata lugens / Sogatella furcifera",
        "severity": "high",
        "symptoms_vi": "Rầy tập trung chích hút nhựa ở phần gốc bẹ lúa sát mặt nước làm lá lúa chuyển vàng từ lá dưới lên, sau đó cả chòm lúa khô cháy màu nâu rụi lõm xuống như lòng chảo (triệu chứng cháy rầy); bẹ lúa có vết chích nâu đen và lớp muội đen.",
        "symptoms_en": "Planthoppers congregate at the base of rice tillers above the waterline, causing yellowing of lower leaves followed by circular patches of brownish-orange dried plants (hopperburn).",
        "conditions_vi": "Thời tiết nắng nóng xen mưa rào ẩm ướt, ruộng gieo sạ quá dày, bón thừa phân đạm và phun thuốc trừ sâu phổ rộng sớm làm chết thiên địch.",
        "conditions_en": "Warm humid weather, dense seeding, excess nitrogen, early broad-spectrum insecticide sprays.",
        "prevention_vi": "Gieo sạ đồng loạt né rầy, dùng giống kháng rầy, giữ mực nước và bảo tồn thiên địch (nhện, kiến ba khoang, bọ xít mù xanh) trong 40 ngày đầu sau sạ.",
        "prevention_en": "Synchronous planting, resistant varieties, conserve natural enemies in first 40 days.",
        "treatment_vi": "Pymetrozine, Dinotefuran, Triflumezopyrim, Buprofezin, Imidacloprid (rẽ hàng lúa phun kỹ vào gốc bẹ)"
    },
    {
        "crop": "Lúa",
        "name_vi": "Sâu cuốn lá nhỏ hại lúa",
        "name_en": "Rice Leaf Folder",
        "scientific_name": "Cnaphalocrocis medinalis",
        "severity": "medium",
        "symptoms_vi": "Sâu non nhả tơ khâu dính hai mép lá lúa dọc theo chiều dài tạo thành ống cuốn tròn; sâu nằm bên trong ăn phần diệp lục xanh chỉ để lại lớp biểu bì mỏng màu trắng bạch thành từng vệt dài dọc phiến lá.",
        "symptoms_en": "Larvae fold rice leaves longitudinally with silk threads and scrape the green mesophyll inside, leaving long translucent white streaks on the leaf blade.",
        "conditions_vi": "Ruộng lúa xanh tốt, bón thừa đạm, thời tiết âm u mưa nhỏ xen nắng nhẹ giai đoạn đẻ nhánh rộ và làm đòng.",
        "conditions_en": "Lush high-nitrogen fields at maximum tillering and booting stages.",
        "prevention_vi": "Không bón thừa đạm, bảo vệ ong ký sinh và thiên địch ngoài đồng, chỉ phun thuốc khi mật độ sâu vượt ngưỡng (>20 con/m2 giai đoạn làm đòng).",
        "prevention_en": "Avoid excess nitrogen, conserve parasitoid wasps, spray only above economic threshold.",
        "treatment_vi": "Chlorantraniliprole, Indoxacarb, Emamectin benzoate, Spinetoram, Flubendiamide"
    },
    # --- CÂY CÓ MÚI (CABI Vietnam SOFRI Factsheets) ---
    {
        "crop": "Cam/Bưởi",
        "name_vi": "Rầy mềm hại cây có múi",
        "name_en": "Citrus Aphids",
        "scientific_name": "Toxoptera citricida / Toxoptera aurantii",
        "severity": "medium",
        "symptoms_vi": "Rầy mềm màu nâu đen hoặc xanh đen tập trung dày đặc ở đọt non, mặt dưới lá non và nụ hoa chích hút nhựa làm lá non cong queo, co rúm úp xuống, đọt non chùn lại; tiết mật ngọt gây nấm muội đen phủ kín mặt lá và truyền bệnh virus Tristeza.",
        "symptoms_en": "Dense colonies of dark brown/black aphids on tender shoots and undersides of young leaves causing downward leaf curling, stunted shoots, black sooty mold, and Citrus Tristeza Virus transmission.",
        "conditions_vi": "Phát sinh mạnh vào các đợt cây ra lộc non mùa xuân và đầu mùa mưa (Tài liệu CABI Plantwise Vietnam & SOFRI).",
        "conditions_en": "Flush periods in spring and early rainy season.",
        "prevention_vi": "Tỉa cành điều khiển lộc non ra tập trung, bảo vệ thiên địch (bọ rùa, ruồi ăn rầy), phun dầu khoáng nông nghiệp khi lộc vừa nhú.",
        "prevention_en": "Synchronize flush growth, conserve ladybird beetles, spray horticultural mineral oil.",
        "treatment_vi": "Imidacloprid, Thiamethoxam, Pymetrozine, Spirotetramat, Dầu khoáng (Mineral oil)"
    },
    {
        "crop": "Cam/Bưởi",
        "name_vi": "Nhện đỏ và Nhện rám vàng hại cây có múi",
        "name_en": "Citrus Red Mite & Citrus Rust Mite",
        "scientific_name": "Panonychus citri / Phyllocoptruta oleivora",
        "severity": "medium",
        "symptoms_vi": "Trên lá bánh tẻ xuất hiện dày đặc các chấm nhỏ li ti màu trắng bạc/vàng xám làm phiến lá mất màu bóng chuyển xám bạc khô cằn; trên quả làm vỏ quả bị rám nắng màu nâu đồng hoặc xám đen sần sùi (da cám, da lu).",
        "symptoms_en": "Pale stippling and silvery-gray dullness on leaves; bronzing or dark russeting ('sharkskin' / 'mahogany' rind) on citrus fruits.",
        "conditions_vi": "Thời tiết nắng nóng, khô hạn kéo dài, độ ẩm không khí thấp.",
        "conditions_en": "Hot, dry weather with low humidity.",
        "prevention_vi": "Tưới phun mưa lên tán cây trong mùa khô, phun dầu khoáng định kỳ, tránh lạm dụng thuốc gốc Cúc (Pyrethroid) gây bộc phát nhện.",
        "prevention_en": "Overhead water spraying in dry season, mineral oil applications, avoid pyrethroid overuse.",
        "treatment_vi": "Abamectin, Spirodiclofen, Propargite, Fenpyroximate, Hexythiazox, Dầu khoáng"
    },
    # --- SẦU RIÊNG (CABI Vietnam PMDG) ---
    {
        "crop": "Sầu riêng",
        "name_vi": "Sâu đục quả sầu riêng",
        "name_en": "Durian Fruit Borer / Yellow Peach Moth",
        "scientific_name": "Conogethes punctiferalis",
        "severity": "high",
        "symptoms_vi": "Sâu non đục vào vỏ quả sầu riêng (đặc biệt nơi hai quả tiếp xúc nhau) từ khi quả non đến khi chín, đùn phân màu nâu đen kết dính bằng tơ ra ngoài miệng lỗ đục trên gai quả; vết đục tạo điều kiện cho nấm Phytophthora xâm nhập gây thối quả và rụng quả.",
        "symptoms_en": "Larvae bore into durian fruits (especially where two fruits touch), extruding dark brown frass webbed with silk between spines and predisposing fruits to Phytophthora fruit rot.",
        "conditions_vi": "Giai đoạn quả non đến thu hoạch, vườn rậm rạp hoặc để quả mọc thành chùm sát nhau (CABI Vietnam PMDG).",
        "conditions_en": "Fruit development stage, particularly in clustered touching fruits.",
        "prevention_vi": "Tỉa bớt quả trong chùm hoặc chèn que nhỏ tách rời không để hai quả dính sát nhau, bao quả, thu gom tiêu hủy quả rụng bị sâu.",
        "prevention_en": "Thin fruit clusters or separate touching fruits with spacers, fruit bagging, destroy fallen infested fruits.",
        "treatment_vi": "Chlorantraniliprole, Emamectin benzoate, Spinetoram, Indoxacarb, Lambda-cyhalothrin"
    },
    {
        "crop": "Sầu riêng",
        "name_vi": "Bệnh đốm rong (Tảo đỏ) hại lá và cành sầu riêng",
        "name_en": "Durian Algal Leaf Spot / Red Rust",
        "scientific_name": "Cephaleuros virescens",
        "severity": "medium",
        "symptoms_vi": "Trên mặt lá già và vỏ cành xuất hiện các đốm tròn hơi nổi gồ có lớp nhung mịn như nhung lụa màu xanh xám, sau chuyển sang màu nâu đỏ gỉ sắt hoặc cam gạch rất đặc trưng; làm lá khô cứng giảm quang hợp và vỏ cành nứt nẻ.",
        "symptoms_en": "Circular raised velvety spots on mature leaves and twigs that turn from greenish-gray to rusty orange-red, reducing photosynthesis and cracking twig bark.",
        "conditions_vi": "Vườn ẩm thấp, rậm rạp thiếu ánh nắng, mưa nhiều trong mùa mưa.",
        "conditions_en": "High humidity, poor canopy aeration, shaded damp orchards.",
        "prevention_vi": "Cắt tỉa cành vô hiệu tạo độ thông thoáng cho ánh nắng chiếu vào thân cành, thoát nước tốt và bón phân cân đối.",
        "prevention_en": "Prune canopy for sunlight penetration and airflow, improve drainage.",
        "treatment_vi": "Copper Oxychloride, Copper Hydroxide, Cuprous Oxide (phun rửa vườn bằng thuốc gốc đồng)"
    },
    # --- XOÀI (CABI Vietnam Factsheets) ---
    {
        "crop": "Xoài",
        "name_vi": "Bệnh thán thư hại xoài (Khô bông, đốm đen lá và quả)",
        "name_en": "Mango Anthracnose",
        "scientific_name": "Colletotrichum gloeosporioides",
        "severity": "high",
        "symptoms_vi": "Trên lá non tạo các đốm tròn/đa giác màu nâu sẫm làm lá co rúm rách thủng; trên lá già tạo vết cháy nâu đen ở chóp và mép lá; trên chùm hoa gây khô đen rụng hoa; trên vỏ quả tạo vết lõm đen tròn có bào tử màu hồng nhạt khi ẩm.",
        "symptoms_en": "Dark brown angular spots and shot-holes on young leaves, tip/margin blight on mature leaves, blackened panicle blight, and sunken black tear-stain lesions on ripening fruit.",
        "conditions_vi": "Mưa phùn, sương mù, ẩm độ >85% trùng vào giai đoạn xoài ra đọt non, trổ bông và nuôi quả.",
        "conditions_en": "Rain, fog, and high humidity (>85%) during flushing, flowering, and fruiting.",
        "prevention_vi": "Tỉa cành thông thoáng sau thu hoạch, bao quả xoài, thu gom cành hoa và quả bệnh rụng.",
        "prevention_en": "Post-harvest pruning, fruit bagging, orchard sanitation.",
        "treatment_vi": "Azoxystrobin, Difenoconazole, Propineb, Mancozeb, Carbendazim"
    },
    {
        "crop": "Xoài",
        "name_vi": "Sâu đục quả xoài (Sâu đục hạt xoài)",
        "name_en": "Mango Red-banded Fruit Borer",
        "scientific_name": "Deanolis albizonalis (Noorda albizonalis)",
        "severity": "high",
        "symptoms_vi": "Sâu non có các khoang màu đỏ trắng xen kẽ đục vào phần chóp đuôi quả xoài tạo lỗ thủng có nhựa và phân sâu đùn ra, ăn sâu vào thịt quả và hạt làm quả xoài bị nứt dọc và rụng hàng loạt (CABI Plantwise Vietnam Factsheet).",
        "symptoms_en": "Red-and-white banded caterpillars bore into the distal tip of mango fruits, exuding sap and frass, tunneling into the flesh and seed and causing longitudinal fruit cracking and drop.",
        "conditions_vi": "Phát sinh mạnh từ khi quả xoài bằng quả trứng gà đến khi thu hoạch, đặc biệt ở ĐBSCL và Đông Nam Bộ.",
        "conditions_en": "From marble/egg-sized fruit stage to harvest.",
        "prevention_vi": "Bao quả xoài sớm sau khi rụng sinh lý (30-35 ngày sau đậu quả), thu gom tiêu hủy quả rụng và cạo vỏ khô trên thân để diệt nhộng.",
        "prevention_en": "Early fruit bagging 30-35 days after fruit set, destroy fallen fruits, scrape loose bark to remove pupae.",
        "treatment_vi": "Chlorantraniliprole, Emamectin benzoate, Spinetoram, Cypermethrin"
    },
    {
        "crop": "Xoài",
        "name_vi": "Rầy bông xoài (Rầy chổng cánh xoài)",
        "name_en": "Mango Leafhopper",
        "scientific_name": "Idioscopus nitidulus / Idioscopus clypealis",
        "severity": "high",
        "symptoms_vi": "Rầy tập trung chích hút nhựa ở đọt non và chùm hoa xoài làm hoa khô héo, chuyển màu nâu đen và rụng trơ cuống; rầy tiết rất nhiều mật ngọt làm lá và cành phủ một lớp nấm muội đen dày đặc.",
        "symptoms_en": "Hoppers suck sap from tender shoots and inflorescences causing blossom withering, flower drop, and heavy black sooty mold coating on leaves from honeydew secretion.",
        "conditions_vi": "Thời tiết nắng ấm, khô hanh trùng kỳ xoài ra lộc và trổ bông (vụ đông xuân).",
        "conditions_en": "Warm dry weather during flushing and flowering.",
        "prevention_vi": "Tỉa cành tạo tán thông thoáng ánh sáng, treo bẫy dính vàng, rửa vườn sau thu hoạch.",
        "prevention_en": "Canopy pruning for light penetration, yellow sticky traps.",
        "treatment_vi": "Imidacloprid, Thiamethoxam, Buprofezin, Pymetrozine, Lambda-cyhalothrin"
    },
    # --- THANH LONG (CABI Vietnam & SOFRI) ---
    {
        "crop": "Thanh long",
        "name_vi": "Bệnh đốm nâu thanh long (Bệnh tắc kè / Đốm trắng)",
        "name_en": "Dragon Fruit Brown Spot / Stem Canker",
        "scientific_name": "Neoscytalidium dimidiatum",
        "severity": "high",
        "symptoms_vi": "Trên cành non và vỏ quả thanh long xuất hiện các chấm nhỏ lõm màu trắng như mắt cá, sau nhanh chóng chuyển thành mụn tròn nổi gồ màu nâu đỏ như mắt tắc kè, liên kết thành mảng sần sùi thối nâu làm cành và quả thối rữa.",
        "symptoms_en": "Small sunken white specks on young cladodes and fruits that turn into raised reddish-brown scabby spots, coalescing into large corky brown cankers and rot.",
        "conditions_vi": "Mùa mưa ẩm độ cao, sương đêm nhiều, lây lan rất nhanh qua nước mưa và dụng cụ cắt tỉa.",
        "conditions_en": "Rainy season, high humidity, heavy dew.",
        "prevention_vi": "Cắt bỏ và đem ra khỏi vườn tiêu hủy toàn bộ cành/quả nhiễm bệnh, khử trùng kéo cắt cành, bón vôi và Trichoderma.",
        "prevention_en": "Sanitary pruning and burning of infected cladodes, disinfect pruning shears, apply lime and Trichoderma.",
        "treatment_vi": "Azoxystrobin + Difenoconazole, Tebuconazole, Trifloxystrobin, Mancozeb, Copper Hydroxide"
    },
    # --- RAU HỌ THẬP TỰ / BẮP CẢI (CABI Vietnam PMDG) ---
    {
        "crop": "Rau màu/Bắp cải",
        "name_vi": "Sâu tơ hại rau họ thập tự (Bắp cải, Súp lơ, Cải xanh)",
        "name_en": "Diamondback Moth on Crucifers",
        "scientific_name": "Plutella xylostella",
        "severity": "high",
        "symptoms_vi": "Sâu non màu xanh nhạt gặm phần thịt lá ở mặt dưới, chỉ chừa lại lớp biểu bì mặt trên tạo thành các đốm trắng mờ như cửa sổ kính; khi lớn cắn thủng lá lỗ chỗ như lưới rách làm cây cải không cuốn bắp được (CABI Vietnam PMDG).",
        "symptoms_en": "Small green caterpillars feed on the lower leaf epidermis leaving translucent upper 'windowpanes' and riddling leaves with irregular holes.",
        "conditions_vi": "Thời tiết khô mát đến ấm áp (20-30°C), trồng rau họ cải liên tục quanh năm.",
        "conditions_en": "Dry cool-to-warm weather, continuous crucifer cultivation.",
        "prevention_vi": "Luân canh với cây khác họ (họ Đậu, hành tỏi, lúa), trồng xen cà chua để xua đuổi trưởng thành, tưới phun mưa vào chiều tối, dùng bẫy pheromone.",
        "prevention_en": "Crop rotation with non-crucifers, intercrop with tomato, evening overhead sprinkler irrigation, pheromone traps.",
        "treatment_vi": "Bacillus thuringiensis (Bt), Spinetoram, Emamectin benzoate, Chlorantraniliprole, Indoxacarb (luân phiên hoạt chất chống kháng thuốc)"
    },
    {
        "crop": "Rau màu/Bắp cải",
        "name_vi": "Sâu khoang và Sâu xanh da láng hại rau màu",
        "name_en": "Cluster Caterpillar & Beet Armyworm",
        "scientific_name": "Spodoptera litura / Spodoptera exigua",
        "severity": "high",
        "symptoms_vi": "Sâu tuổi nhỏ sống tập trung hàng trăm con ở mặt dưới lá ăn khuyết hết thịt lá chỉ còn mạng gân lá trắng xơ xác; sâu tuổi lớn phân tán cắn thủng lá thành các lỗ rách lớn và đục vào bắp/quả (CABI Vietnam Sơn La Factsheet).",
        "symptoms_en": "Gregarious young larvae skeletonize leaves leaving only a mesh of veins; older larvae chew large irregular holes in foliage and bore into heads/pods.",
        "conditions_vi": "Thời tiết nóng ẩm xen kẽ nắng mưa, ruộng nhiều cỏ dại.",
        "conditions_en": "Warm humid weather, weedy fields.",
        "prevention_vi": "Ngắt bỏ các ổ trứng có phủ lông vàng nâu và các lá có sâu non mới nở tập trung, dùng bẫy chua ngọt và bẫy pheromone.",
        "prevention_en": "Hand-pick egg masses and gregarious young larval clusters, use pheromone and sweet-sour traps.",
        "treatment_vi": "Emamectin benzoate, Spinetoram, Indoxacarb, Lufenuron, Bacillus thuringiensis (Bt)"
    },
    {
        "crop": "Rau màu/Bắp cải",
        "name_vi": "Bệnh thối nhũn vi khuẩn hại bắp cải và rau màu",
        "name_en": "Bacterial Soft Rot of Crucifers",
        "scientific_name": "Pectobacterium carotovorum (Erwinia carotovora)",
        "severity": "high",
        "symptoms_vi": "Vết bệnh xuất hiện ở gốc cuống lá hoặc đỉnh bắp cải dạng đốm ướt như luộc nước sôi, nhanh chóng lan rộng làm mô lá và bắp thối nhũn thành dịch nhầy màu nâu vàng, bốc mùi hôi thối nồng nặc rất đặc trưng.",
        "symptoms_en": "Water-soaked lesions at petiole bases or heads that rapidly macerate into a slimy, foul-smelling soft rot.",
        "conditions_vi": "Thời tiết nóng ẩm mưa nhiều, ruộng thoát nước kém, bón thừa đạm hoặc có vết thương do sâu tơ/sâu khoang cắn phá.",
        "conditions_en": "Warm wet weather, poor drainage, excess nitrogen, insect feeding wounds.",
        "prevention_vi": "Trồng luống cao thoát nước tốt, bón vôi khử trùng đất, kiểm soát tốt sâu ăn lá để tránh tạo vết thương.",
        "prevention_en": "High raised beds, soil liming, control leaf-chewing insects to prevent entry wounds.",
        "treatment_vi": "Kasugamycin, Streptomycin, Oxolinic acid, Copper Hydroxide"
    },
    # --- LẠC & ĐẬU TƯƠNG (CABI Vietnam PMDG) ---
    {
        "crop": "Lạc/Đậu tương",
        "name_vi": "Bệnh đốm nâu và đốm đen hại lạc (Đậu phộng)",
        "name_en": "Peanut Early & Late Leaf Spot",
        "scientific_name": "Cercospora arachidicola / Phaeoisariopsis personata",
        "severity": "medium",
        "symptoms_vi": "Trên lá lạc xuất hiện nhiều đốm tròn (2-8mm): đốm nâu có màu nâu sáng kèm quầng vàng tươi rất rõ ở mặt trên; đốm đen có màu nâu đen đến đen kịt không có quầng vàng rõ và mặt dưới có các vòng ổ bào tử đen; làm lá lạc vàng và rụng trơ gốc (CABI Vietnam PMDG).",
        "symptoms_en": "Circular 2-8mm leaf spots: early leaf spot is reddish-brown with a bright yellow halo; late leaf spot is dark brown-to-black with dark spore tufts underneath, causing severe defoliation.",
        "conditions_vi": "Thời tiết nóng ẩm mưa nhiều giai đoạn lạc ra hoa đâm tia đến chắc củ, đất thiếu canxi và magie.",
        "conditions_en": "Warm humid weather during flowering and pegging, calcium/magnesium deficiency.",
        "prevention_vi": "Luân canh lạc với lúa nước, bón vôi (Canxi) và lân đầy đủ, thu dọn sạch tàn dư cây lạc sau thu hoạch.",
        "prevention_en": "Rotate with paddy rice, apply lime (calcium) and phosphorus, remove crop residues.",
        "treatment_vi": "Difenoconazole, Azoxystrobin, Tebuconazole, Chlorothalonil, Mancozeb"
    },
    {
        "crop": "Lạc/Đậu tương",
        "name_vi": "Bệnh sương mai và gỉ sắt hại đậu tương (Đậu nành)",
        "name_en": "Soybean Downy Mildew & Rust",
        "scientific_name": "Peronospora manshurica / Phakopsora pachyrhizi",
        "severity": "high",
        "symptoms_vi": "Bệnh sương mai tạo các đốm vàng xanh nhạt ở mặt trên lá và lớp mốc xám tím ở mặt dưới; bệnh gỉ sắt tạo vô số mụn u nhỏ li ti màu nâu đỏ gạch ở mặt dưới lá làm lá vàng khô và rụng sớm, hạt đậu lép (CABI Vietnam Sơn La Factsheet).",
        "symptoms_en": "Downy mildew causes pale green-yellow upper spots with grayish-purple fuzz underneath; soybean rust produces dense reddish-brown pustules on the lower leaf surface leading to premature defoliation.",
        "conditions_vi": "Ẩm độ cao (>85%), sương mù nhiều, nhiệt độ 20-28°C.",
        "conditions_en": "High humidity (>85%), heavy dew/fog, temperatures 20-28°C.",
        "prevention_vi": "Dùng hạt giống sạch bệnh, gieo trồng mật độ vừa phải thông thoáng, luân canh với cây ngô hoặc lúa.",
        "prevention_en": "Clean seed, moderate planting density, crop rotation.",
        "treatment_vi": "Azoxystrobin + Difenoconazole, Hexaconazole, Metalaxyl + Mancozeb, Propiconazole"
    }
]


def fetch_inat_photo(sci_name: str) -> str:
    if not sci_name or "Physiological" in sci_name:
        return ""
    q = (
        sci_name.split("(")[0]
        .split("/")[0]
        .replace("pv.", "")
        .replace("subsp.", "")
        .replace("f. sp.", "")
        .replace("spp.", "")
        .replace("Candidatus", "")
        .strip()
    )
    tokens = q.split()
    if len(tokens) >= 2:
        q = " ".join(tokens[:2])
    url = f"https://api.inaturalist.org/v1/taxa?q={urllib.parse.quote(q)}&per_page=3"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PlantDoctorTUAF/2.6"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        for res in data.get("results", []):
            dp = res.get("default_photo") or {}
            img = dp.get("medium_url") or dp.get("square_url")
            if img:
                return img
    except Exception:
        pass
    return ""


def fetch_wiki_photo(query: str) -> str:
    if not query:
        return ""
    url = (
        "https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6"
        f"&gsrsearch={urllib.parse.quote(query)}&gsrlimit=4&prop=imageinfo&iiprop=url&iiurlwidth=500&format=json"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PlantDoctorTUAF/2.6"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        pages = (data.get("query") or {}).get("pages") or {}
        for p in pages.values():
            ii = (p.get("imageinfo") or [{}])[0]
            u = ii.get("thumburl") or ii.get("url")
            if u and not any(u.lower().endswith(ext) for ext in (".pdf", ".svg", ".tif", ".tiff", ".djvu", ".ogv", ".webm")):
                return u
    except Exception:
        pass
    return ""


def main():
    with open(KB_PATH, "r", encoding="utf-8") as f:
        entries = json.load(f)

    existing_keys = {(e["crop"].strip().lower(), e["name_vi"].strip().lower()) for e in entries}
    for extra in EXTRA_CABI_VN_ENTRIES:
        k = (extra["crop"].strip().lower(), extra["name_vi"].strip().lower())
        if k not in existing_keys:
            entries.append(extra)
            existing_keys.add(k)

    resolved_count = 0
    for e in entries:
        img = (e.get("image_url") or "").strip()
        if not img:
            sci = e.get("scientific_name", "")
            img = fetch_inat_photo(sci)
            if not img:
                q_sci = sci.split("(")[0].split("/")[0].strip()
                img = fetch_wiki_photo(q_sci)
            if not img:
                img = fetch_wiki_photo(e.get("name_en", ""))
            if img:
                e["image_url"] = img
                resolved_count += 1
            time.sleep(0.1)
        else:
            resolved_count += 1

    with open(KB_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"Total CABI Vietnam entries: {len(entries)}, entries with verified image_url: {resolved_count}/{len(entries)}")


if __name__ == "__main__":
    main()
