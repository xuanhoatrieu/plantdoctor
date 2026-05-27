import { useState, useEffect } from 'react';
import { View, Text, FlatList, Image, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function HistoryScreen() {
  const [history, setHistory] = useState([]);

  const load = () => AsyncStorage.getItem('history').then(d => { if (d) setHistory(JSON.parse(d)); });
  useEffect(() => { load(); }, []);

  const clear = () => {
    Alert.alert('Xác nhận', 'Xóa toàn bộ lịch sử?', [
      { text: 'Hủy', style: 'cancel' },
      { text: 'Xóa', style: 'destructive', onPress: () => { AsyncStorage.removeItem('history'); setHistory([]); } },
    ]);
  };

  return (
    <SafeAreaView style={s.container}>
      <View style={s.header}>
        <Text style={s.title}>📜 Lịch sử chẩn đoán</Text>
        {history.length > 0 && <TouchableOpacity onPress={clear}><Text style={s.clearBtn}>Xóa tất cả</Text></TouchableOpacity>}
      </View>
      {history.length === 0 ? (
        <View style={s.empty}><Text style={s.emptyText}>Chưa có lịch sử chẩn đoán</Text></View>
      ) : (
        <FlatList
          data={history}
          keyExtractor={(_, i) => String(i)}
          contentContainerStyle={{ padding: 16 }}
          renderItem={({ item }) => {
            const p = item.result?.predictions?.[0];
            if (!p) return null;
            const isHealthy = p.label?.toLowerCase().includes('healthy') || p.label?.includes('Khỏe mạnh');
            return (
              <View style={[s.item, isHealthy ? s.itemOk : s.itemBad]}>
                {item.imageUri && <Image source={{ uri: item.imageUri }} style={s.thumb} />}
                <View style={s.info}>
                  <Text style={s.name} numberOfLines={2}>{p.name}</Text>
                  <Text style={s.date}>{new Date(item.date).toLocaleString()}</Text>
                </View>
                <Text style={s.conf}>{p.confidence}%</Text>
              </View>
            );
          }}
        />
      )}
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 20, paddingBottom: 10 },
  title: { fontSize: 18, fontWeight: 'bold', color: '#111' },
  clearBtn: { color: '#ef4444', fontSize: 14, fontWeight: '500' },
  empty: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  emptyText: { color: '#9ca3af', fontSize: 15 },
  item: { flexDirection: 'row', alignItems: 'center', padding: 12, marginBottom: 10, borderRadius: 14, borderWidth: 1 },
  itemOk: { backgroundColor: '#f0fdf4', borderColor: '#86efac' },
  itemBad: { backgroundColor: '#fef2f2', borderColor: '#fca5a5' },
  thumb: { width: 50, height: 50, borderRadius: 10, marginRight: 12 },
  info: { flex: 1 },
  name: { fontWeight: '600', color: '#111', fontSize: 14 },
  date: { fontSize: 11, color: '#9ca3af', marginTop: 3 },
  conf: { fontWeight: '700', color: '#666', fontSize: 14 },
});
