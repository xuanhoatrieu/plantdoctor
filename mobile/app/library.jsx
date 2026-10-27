import { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, Image, TextInput, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

const API_URL = 'https://benhcay.tuaf.edu.vn';

const CROP_ICONS = {
  'Chè': '🍵',
  'Cam/Bưởi': '🍊',
  'Lúa': '🌾',
  'Ngô': '🌽',
  'Cà phê': '☕',
  'Hồ tiêu/Ớt': '🌶️',
  'Sầu riêng': '🍈',
  'Cà chua': '🍅',
  'Khoai tây': '🥔',
  'Chuối': '🍌',
  'Nhãn/Vải': '🍒',
  'Xoài': '🥭',
  'Thanh long': '🌵',
  'Rau màu/Bắp cải': '🥬',
  'Lạc/Đậu tương': '🥜',
};

export default function LibraryScreen() {
  const [subTab, setSubTab] = useState('guide'); // 'guide' | 'diseases'
  const [cropGuides, setCropGuides] = useState([]);
  const [diseases, setDiseases] = useState([]);
  const [selectedCrop, setSelectedCrop] = useState('Lúa');
  const [cropFilter, setCropFilter] = useState('');
  const [search, setSearch] = useState('');
  const [expanded, setExpanded] = useState(null);
  const [fromStageCrop, setFromStageCrop] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/api/v1/crop-guides`)
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setCropGuides(data);
        }
      })
      .catch(() => {});

    fetch(`${API_URL}/api/v1/diseases`)
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setDiseases(data);
        }
      })
      .catch(() => {});
  }, []);

  const openDiseaseFromStage = (cropName, diseaseNameVi) => {
    setFromStageCrop(cropName);
    setCropFilter(cropName);
    setSearch('');
    setExpanded(`${cropName}::${diseaseNameVi}`);
    setSubTab('diseases');
  };

  const activeGuide = cropGuides.find((g) => g.crop === selectedCrop) || cropGuides[0] || null;

  const groupedDiseases = (() => {
    const map = new Map();
    for (const d of diseases) {
      if (cropFilter && d.crop !== cropFilter) continue;
      if (search.trim()) {
        const q = search.toLowerCase();
        const match =
          (d.name_vi || '').toLowerCase().includes(q) ||
          (d.scientific_name || '').toLowerCase().includes(q) ||
          (d.symptoms_vi || '').toLowerCase().includes(q);
        if (!match) continue;
      }
      if (!map.has(d.crop)) map.set(d.crop, []);
      map.get(d.crop).push(d);
    }
    return Array.from(map.entries());
  })();

  return (
    <SafeAreaView style={s.container}>
      <ScrollView contentContainerStyle={s.scroll}>
        <Text style={s.title}>📚 Cẩm nang cây trồng & bệnh hại</Text>

        {/* 2 Sub-tabs */}
        <View style={s.tabBar}>
          <TouchableOpacity
            style={[s.tabBtn, subTab === 'guide' && s.tabBtnActive]}
            onPress={() => setSubTab('guide')}
          >
            <Text style={[s.tabBtnText, subTab === 'guide' && s.tabBtnTextActive]}>
              🌱 Quy trình trồng
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[s.tabBtn, subTab === 'diseases' && s.tabBtnActive]}
            onPress={() => setSubTab('diseases')}
          >
            <Text style={[s.tabBtnText, subTab === 'diseases' && s.tabBtnTextActive]}>
              🔬 Danh mục bệnh ({diseases.length || 50})
            </Text>
          </TouchableOpacity>
        </View>

        {subTab === 'guide' ? (
          <View>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.cropScroll}>
              {cropGuides.map((g) => {
                const active = activeGuide && activeGuide.crop === g.crop;
                return (
                  <TouchableOpacity
                    key={g.crop}
                    style={[s.cropChip, active && s.cropChipActive]}
                    onPress={() => setSelectedCrop(g.crop)}
                  >
                    <Text style={[s.cropChipText, active && s.cropChipTextActive]}>
                      {CROP_ICONS[g.crop] || '🌿'} {g.crop}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </ScrollView>

            {activeGuide ? (
              <View>
                <View style={s.guideHeader}>
                  <Text style={s.guideHeaderTitle}>
                    {CROP_ICONS[activeGuide.crop] || '🌿'} Quy trình canh tác: {activeGuide.crop}
                  </Text>
                  {!!activeGuide.scientific_name && (
                    <Text style={s.guideSci}>🧬 {activeGuide.scientific_name}</Text>
                  )}
                  {!!activeGuide.source_agency && (
                    <Text style={s.guideSource}>🏛️ {activeGuide.source_agency}</Text>
                  )}
                  <Text style={s.guideSummary}>{activeGuide.summary_vi}</Text>
                </View>

                {(activeGuide.stages || []).map((st) => (
                  <View key={st.stage_number} style={s.stageCard}>
                    <View style={s.stageHeader}>
                      <Text style={s.stageTitle}>{st.title_vi}</Text>
                      <Text style={s.stageTiming}>🕒 {st.timing_vi}</Text>
                    </View>
                    <View style={s.careBox}>
                      <Text style={s.careLabel}>🌱 Kỹ thuật chăm sóc & Bón phân:</Text>
                      <Text style={s.careText}>{st.care_vi}</Text>
                    </View>
                    {!!st.notes_vi && (
                      <View style={s.noteBox}>
                        <Text style={s.noteLabel}>⚠️ Chú ý quan trọng:</Text>
                        <Text style={s.noteText}>{st.notes_vi}</Text>
                      </View>
                    )}
                    {st.linked_diseases?.length > 0 && (
                      <View style={{ marginTop: 8 }}>
                        <Text style={s.linkedHeader}>
                          🐛 Bệnh thường gặp giai đoạn này (nhấn để xem chi tiết):
                        </Text>
                        {st.linked_diseases.map((ld, idx) => (
                          <TouchableOpacity
                            key={idx}
                            style={s.linkedBtn}
                            onPress={() => openDiseaseFromStage(activeGuide.crop, ld.name_vi)}
                          >
                            {!!ld.image_url && (
                              <Image
                                source={{ uri: ld.image_url.startsWith('http') ? ld.image_url : `${API_URL}${ld.image_url}` }}
                                style={s.linkedThumb}
                              />
                            )}
                            <View style={{ flex: 1 }}>
                              <Text style={s.linkedName}>{ld.name_vi}</Text>
                              <Text style={s.linkedAction}>Xem triệu chứng & thuốc đặc trị →</Text>
                            </View>
                          </TouchableOpacity>
                        ))}
                      </View>
                    )}
                  </View>
                ))}
              </View>
            ) : (
              <Text style={s.loadingText}>Đang tải quy trình trồng trọt...</Text>
            )}
          </View>
        ) : (
          <View>
            {!!fromStageCrop && (
              <TouchableOpacity
                style={s.backBanner}
                onPress={() => {
                  setSelectedCrop(fromStageCrop);
                  setSubTab('guide');
                }}
              >
                <Text style={s.backBannerText}>
                  ← Quay lại Quy trình trồng {fromStageCrop}
                </Text>
              </TouchableOpacity>
            )}

            <TextInput
              value={search}
              onChangeText={setSearch}
              placeholder="🔍 Tìm tên bệnh, tác nhân khoa học, triệu chứng..."
              style={s.searchInput}
            />

            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.cropScroll}>
              <TouchableOpacity
                style={[s.cropChip, !cropFilter && s.cropChipActive]}
                onPress={() => {
                  setCropFilter('');
                  setFromStageCrop(null);
                }}
              >
                <Text style={[s.cropChipText, !cropFilter && s.cropChipTextActive]}>
                  Tất cả ({diseases.length})
                </Text>
              </TouchableOpacity>
              {Object.keys(CROP_ICONS).map((c) => (
                <TouchableOpacity
                  key={c}
                  style={[s.cropChip, cropFilter === c && s.cropChipActive]}
                  onPress={() => {
                    setCropFilter(c);
                    setFromStageCrop(null);
                  }}
                >
                  <Text style={[s.cropChipText, cropFilter === c && s.cropChipTextActive]}>
                    {CROP_ICONS[c]} {c}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            {groupedDiseases.map(([cropName, items]) => (
              <View key={cropName} style={s.group}>
                <Text style={s.cropTitle}>
                  {CROP_ICONS[cropName] || '🌿'} {cropName} ({items.length})
                </Text>
                {items.map((d) => {
                  const key = `${cropName}::${d.name_vi}`;
                  const open = expanded === key;
                  const imgUri = d.image_url
                    ? d.image_url.startsWith('http')
                      ? d.image_url
                      : `${API_URL}${d.image_url}`
                    : null;
                  return (
                    <TouchableOpacity
                      key={key}
                      style={[s.card, open && s.cardHighlight]}
                      onPress={() => setExpanded(open ? null : key)}
                      activeOpacity={0.8}
                    >
                      <View style={s.cardRow}>
                        <Text style={s.cardName}>{d.name_vi}</Text>
                        <Text>{d.severity === 'high' ? '🔴' : d.severity === 'low' ? '🟢' : '🟠'}</Text>
                      </View>
                      {open && (
                        <View style={s.cardBody}>
                          {!!imgUri && <Image source={{ uri: imgUri }} style={s.diseaseImg} />}
                          {!!d.scientific_name && (
                            <Text style={s.sciText}>🧬 {d.scientific_name}</Text>
                          )}
                          <Text style={s.desc}>{d.symptoms_vi}</Text>
                          {!!d.prevention_vi && (
                            <View style={s.prevBox}>
                              <Text style={s.prevLabel}>🛡️ Phòng ngừa IPM:</Text>
                              <Text style={s.prevText}>{d.prevention_vi}</Text>
                            </View>
                          )}
                          {!!d.treatment_vi && (
                            <View style={s.treatBox}>
                              <Text style={s.treatLabel}>💊 Hoạt chất / Điều trị:</Text>
                              <Text style={s.treatText}>{d.treatment_vi}</Text>
                            </View>
                          )}
                        </View>
                      )}
                    </TouchableOpacity>
                  );
                })}
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  scroll: { padding: 16, paddingBottom: 40 },
  title: { fontSize: 18, fontWeight: 'bold', color: '#111', marginBottom: 12 },
  tabBar: { flexDirection: 'row', backgroundColor: '#f3f4f6', borderRadius: 12, padding: 4, marginBottom: 14 },
  tabBtn: { flex: 1, paddingVertical: 10, borderRadius: 9, alignItems: 'center' },
  tabBtnActive: { backgroundColor: '#16a34a' },
  tabBtnText: { fontSize: 13, fontWeight: '700', color: '#4b5563' },
  tabBtnTextActive: { color: '#fff' },
  cropScroll: { marginBottom: 14 },
  cropChip: { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 20, backgroundColor: '#f3f4f6', marginRight: 8, borderWidth: 1, borderColor: '#e5e7eb' },
  cropChipActive: { backgroundColor: '#16a34a', borderColor: '#16a34a' },
  cropChipText: { fontSize: 12, fontWeight: '600', color: '#374151' },
  cropChipTextActive: { color: '#fff' },
  guideHeader: { backgroundColor: '#15803d', borderRadius: 14, padding: 14, marginBottom: 14 },
  guideHeaderTitle: { fontSize: 16, fontWeight: 'bold', color: '#fff' },
  guideSci: { fontSize: 12, fontStyle: 'italic', color: '#dcfce7', marginTop: 2 },
  guideSource: { fontSize: 11, color: '#bbf7d0', marginTop: 4 },
  guideSummary: { fontSize: 13, color: '#f0fdf4', marginTop: 8, lineHeight: 19 },
  stageCard: { backgroundColor: '#fff', borderRadius: 14, padding: 14, marginBottom: 12, borderWidth: 1, borderColor: '#d1fae5' },
  stageHeader: { marginBottom: 8 },
  stageTitle: { fontSize: 14, fontWeight: '700', color: '#111827' },
  stageTiming: { fontSize: 12, color: '#15803d', fontWeight: '600', marginTop: 3 },
  careBox: { backgroundColor: '#f9fafb', padding: 10, borderRadius: 10, marginBottom: 8 },
  careLabel: { fontSize: 12, fontWeight: '700', color: '#166534', marginBottom: 3 },
  careText: { fontSize: 13, color: '#374151', lineHeight: 19 },
  noteBox: { backgroundColor: '#fffbeb', padding: 10, borderRadius: 10, borderWidth: 1, borderColor: '#fde68a' },
  noteLabel: { fontSize: 12, fontWeight: '700', color: '#92400e', marginBottom: 3 },
  noteText: { fontSize: 12, color: '#92400e', lineHeight: 18 },
  linkedHeader: { fontSize: 12, fontWeight: '700', color: '#374151', marginBottom: 6 },
  linkedBtn: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#f0fdf4', padding: 8, borderRadius: 10, marginBottom: 6, borderWidth: 1, borderColor: '#bbf7d0' },
  linkedThumb: { width: 42, height: 42, borderRadius: 8, marginRight: 10, backgroundColor: '#e5e7eb' },
  linkedName: { fontSize: 13, fontWeight: '700', color: '#111827' },
  linkedAction: { fontSize: 11, color: '#15803d', fontWeight: '600', marginTop: 2 },
  backBanner: { backgroundColor: '#dcfce7', padding: 10, borderRadius: 10, marginBottom: 10, borderWidth: 1, borderColor: '#86efac' },
  backBannerText: { fontSize: 13, fontWeight: '700', color: '#166534', textAlign: 'center' },
  searchInput: { borderWidth: 1, borderColor: '#d1d5db', borderRadius: 10, paddingHorizontal: 12, paddingVertical: 9, fontSize: 13, marginBottom: 12 },
  loadingText: { textAlign: 'center', color: '#9ca3af', paddingVertical: 24 },
  group: { marginBottom: 18 },
  cropTitle: { fontSize: 16, fontWeight: 'bold', color: '#166534', marginBottom: 10 },
  card: { backgroundColor: '#f9fafb', borderRadius: 14, padding: 14, marginBottom: 8, borderWidth: 1, borderColor: '#e5e7eb' },
  cardHighlight: { borderColor: '#16a34a', borderWidth: 2, backgroundColor: '#f0fdf4' },
  cardRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardName: { fontWeight: '600', color: '#111', flex: 1, fontSize: 14 },
  cardBody: { marginTop: 10 },
  diseaseImg: { width: '100%', height: 150, borderRadius: 10, marginBottom: 8, backgroundColor: '#e5e7eb' },
  sciText: { fontSize: 12, fontStyle: 'italic', color: '#6b7280', marginBottom: 6 },
  desc: { fontSize: 13, color: '#444', lineHeight: 20, marginBottom: 8 },
  prevBox: { backgroundColor: '#f0fdf4', padding: 10, borderRadius: 10, marginBottom: 8 },
  prevLabel: { fontWeight: '700', color: '#166534', marginBottom: 3, fontSize: 12 },
  prevText: { fontSize: 12, color: '#166534', lineHeight: 18 },
  treatBox: { backgroundColor: '#eff6ff', padding: 10, borderRadius: 10 },
  treatLabel: { fontWeight: '700', color: '#1e40af', marginBottom: 3, fontSize: 12 },
  treatText: { fontSize: 12, color: '#1e40af', lineHeight: 18 },
});
