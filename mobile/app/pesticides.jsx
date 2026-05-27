import { useState, useEffect } from 'react';
import { View, Text, TextInput, FlatList, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import axios from 'axios';

const API_BASE = 'http://10.64.220.241:8001';

const BANNED = ['Aldrin','BHC/Lindane','Cadmium compound','Carbofuran','Chlordane','Chlordimeform','DDT','Dieldrin','Endosulfan','Endrin','Heptachlor','Isobenzan','Isodrin','Lead (Pb)','Methamidophos','Methyl Parathion','Monocrotophos','Parathion Ethyl','Pentachlorophenol','Phosphamidon','Polychlorocamphene','Trichlorfon','Arsenic','Captan','Captafol','Hexachlorobenzene','Mercury','Selenium','Talium','2,4,5-T'];

export default function PesticidesScreen() {
  const [data, setData] = useState(null);
  const [search, setSearch] = useState('');
  const [filtered, setFiltered] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE}/../pesticides.json`).catch(() => null);
    // Load from web public folder via proxy or bundled
    axios.get('http://10.64.220.241:3001/pesticides.json').then(r => {
      setData(r.data);
      setFiltered(r.data.slice(0, 50));
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!data) return;
    if (!search) { setFiltered(data.slice(0, 50)); return; }
    const q = search.toLowerCase();
    setFiltered(data.filter(p => p.n.toLowerCase().includes(q) || p.a.toLowerCase().includes(q) || p.c.toLowerCase().includes(q)).slice(0, 50));
  }, [search, data]);

  return (
    <SafeAreaView style={s.container}>
      <Text style={s.title}>🧪 Thuốc BVTV</Text>

      {/* Banned */}
      <View style={s.bannedBox}>
        <Text style={s.bannedTitle}>🚫 Cấm sử dụng ({BANNED.length} hoạt chất)</Text>
        <Text style={s.bannedText}>{BANNED.join(', ')}</Text>
      </View>

      {/* Search */}
      <TextInput style={s.search} value={search} onChangeText={setSearch} placeholder="Tìm theo tên, hoạt chất, công ty..." />
      <Text style={s.count}>{data ? `${filtered.length} / ${data.length} sản phẩm` : 'Đang tải...'}</Text>

      {/* List */}
      <FlatList
        data={filtered}
        keyExtractor={(_, i) => String(i)}
        renderItem={({ item }) => (
          <View style={s.item}>
            <Text style={s.itemName}>{item.n}</Text>
            <Text style={s.itemDetail}>{item.a}</Text>
            <Text style={s.itemCompany}>{item.c}</Text>
          </View>
        )}
      />
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff', padding: 16 },
  title: { fontSize: 18, fontWeight: 'bold', color: '#111', marginBottom: 12 },
  bannedBox: { backgroundColor: '#fef2f2', borderRadius: 12, padding: 12, marginBottom: 12, borderWidth: 1, borderColor: '#fca5a5' },
  bannedTitle: { fontWeight: '700', color: '#dc2626', marginBottom: 4, fontSize: 13 },
  bannedText: { fontSize: 11, color: '#991b1b', lineHeight: 16 },
  search: { borderWidth: 1, borderColor: '#d1d5db', borderRadius: 12, padding: 12, fontSize: 14, marginBottom: 8, backgroundColor: '#f9fafb' },
  count: { fontSize: 12, color: '#9ca3af', marginBottom: 8 },
  item: { backgroundColor: '#f9fafb', borderRadius: 10, padding: 10, marginBottom: 6, borderWidth: 1, borderColor: '#e5e7eb' },
  itemName: { fontWeight: '600', color: '#111', fontSize: 13 },
  itemDetail: { fontSize: 12, color: '#666', marginTop: 2 },
  itemCompany: { fontSize: 11, color: '#9ca3af', marginTop: 1 },
});
