import { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

const diseases = [
  { crop: '🌾 Lúa', items: [
    { name: 'Bạc lá (Bacterial Blight)', severity: '🔴', desc: 'Lá cháy từ mép vào, chuyển trắng xám. Do Xanthomonas oryzae.', treatment: 'Giống kháng, giảm đạm, Kasugamycin, Bismerthiazol.' },
    { name: 'Đạo ôn (Blast)', severity: '🔴', desc: 'Vết đốm hình mắt én, gãy cổ bông. Do Magnaporthe oryzae.', treatment: 'Tricyclazole (Beam 75WP), Isoprothiolane, giảm đạm.' },
    { name: 'Đốm nâu (Brown Spot)', severity: '🟠', desc: 'Đốm nâu oval trên lá già, đất nghèo dinh dưỡng.', treatment: 'Bón kali + kẽm, Mancozeb, Propiconazole.' },
    { name: 'Vàng lùn (Tungro)', severity: '🔴', desc: 'Lá vàng cam, cây lùn. Virus qua rầy xanh.', treatment: 'Diệt rầy (Imidacloprid), giống kháng, nhổ cây bệnh.' },
  ]},
  { crop: '🌽 Ngô', items: [
    { name: 'Rỉ sắt (Common Rust)', severity: '🟡', desc: 'Mụn bột nâu đỏ trên lá. Do Puccinia sorghi.', treatment: 'Propiconazole, Azoxystrobin, giống kháng.' },
    { name: 'Cháy lá (Northern Leaf Blight)', severity: '🟠', desc: 'Vết bệnh dài hình thuyền. Do Exserohilum turcicum.', treatment: 'Luân canh, Azoxystrobin + Propiconazole.' },
  ]},
  { crop: '🍅 Cà chua', items: [
    { name: 'Héo muộn (Late Blight)', severity: '🔴', desc: 'Vết nâu đen ướt lan nhanh, mốc trắng. Rất nguy hiểm.', treatment: 'Metalaxyl + Mancozeb (Ridomil Gold), Dimethomorph.' },
    { name: 'Virus xoăn lá vàng (TYLCV)', severity: '🔴', desc: 'Lá xoăn vàng, cây còi cọc. Qua bọ phấn trắng.', treatment: 'Diệt bọ phấn, lưới chắn, giống kháng Ty-1/Ty-3.' },
  ]},
  { crop: '🥔 Khoai tây', items: [
    { name: 'Héo muộn (Late Blight)', severity: '🔴', desc: 'Vết nâu đen ướt, lan nhanh khi ẩm. Củ thối nâu.', treatment: 'Metalaxyl + Mancozeb, Cymoxanil, giống kháng.' },
    { name: 'Héo sớm (Early Blight)', severity: '🟡', desc: 'Đốm nâu đồng tâm trên lá già. Do Alternaria solani.', treatment: 'Luân canh, Mancozeb, Chlorothalonil.' },
  ]},
];

export default function LibraryScreen() {
  const [expanded, setExpanded] = useState(null);

  return (
    <SafeAreaView style={s.container}>
      <ScrollView contentContainerStyle={s.scroll}>
        <Text style={s.title}>📚 Thư viện bệnh cây trồng</Text>
        {diseases.map((group, gi) => (
          <View key={gi} style={s.group}>
            <Text style={s.cropTitle}>{group.crop}</Text>
            {group.items.map((d, di) => {
              const key = `${gi}-${di}`;
              const open = expanded === key;
              return (
                <TouchableOpacity key={di} style={s.card} onPress={() => setExpanded(open ? null : key)} activeOpacity={0.7}>
                  <View style={s.cardRow}>
                    <Text style={s.cardName}>{d.name}</Text>
                    <Text>{d.severity}</Text>
                  </View>
                  {open && (
                    <View style={s.cardBody}>
                      <Text style={s.desc}>{d.desc}</Text>
                      <View style={s.treatBox}>
                        <Text style={s.treatLabel}>💊 Điều trị:</Text>
                        <Text style={s.treatText}>{d.treatment}</Text>
                      </View>
                    </View>
                  )}
                </TouchableOpacity>
              );
            })}
          </View>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  scroll: { padding: 20, paddingBottom: 40 },
  title: { fontSize: 18, fontWeight: 'bold', color: '#111', marginBottom: 16 },
  group: { marginBottom: 20 },
  cropTitle: { fontSize: 16, fontWeight: 'bold', color: '#166534', marginBottom: 10 },
  card: { backgroundColor: '#f9fafb', borderRadius: 14, padding: 14, marginBottom: 8, borderWidth: 1, borderColor: '#e5e7eb' },
  cardRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardName: { fontWeight: '600', color: '#111', flex: 1, fontSize: 14 },
  cardBody: { marginTop: 10 },
  desc: { fontSize: 13, color: '#444', lineHeight: 20, marginBottom: 8 },
  treatBox: { backgroundColor: '#eff6ff', padding: 10, borderRadius: 10 },
  treatLabel: { fontWeight: '700', color: '#1e40af', marginBottom: 3 },
  treatText: { fontSize: 13, color: '#1e40af', lineHeight: 20 },
});
