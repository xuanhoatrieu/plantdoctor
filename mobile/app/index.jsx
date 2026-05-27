import { useState, useRef, useEffect } from 'react';
import { View, Text, Image, TouchableOpacity, ScrollView, ActivityIndicator, StyleSheet, Alert, Animated } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SafeAreaView } from 'react-native-safe-area-context';
import { predict } from '../src/api';

function ScanOverlay() {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: 1, duration: 1500, useNativeDriver: true }),
        Animated.timing(anim, { toValue: 0, duration: 1500, useNativeDriver: true }),
      ])
    ).start();
  }, []);
  const translateY = anim.interpolate({ inputRange: [0, 1], outputRange: [0, 220] });
  return (
    <View style={StyleSheet.absoluteFill}>
      <View style={{ ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.3)', borderRadius: 16 }} />
      <Animated.View style={{ position: 'absolute', left: 0, right: 0, height: 3, backgroundColor: '#4ade80', borderRadius: 2, transform: [{ translateY }] }} />
    </View>
  );
}

export default function HomeScreen() {
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const pickImage = async (useCamera) => {
    if (useCamera) {
      const { status } = await ImagePicker.requestCameraPermissionsAsync();
      if (status !== 'granted') { Alert.alert('Cần quyền camera', 'Vui lòng cấp quyền camera trong Cài đặt'); return; }
    } else {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') { Alert.alert('Cần quyền thư viện ảnh', 'Vui lòng cấp quyền trong Cài đặt'); return; }
    }
    const method = useCamera ? ImagePicker.launchCameraAsync : ImagePicker.launchImageLibraryAsync;
    const res = await method({ mediaTypes: ['images'], quality: 0.8 });
    if (!res.canceled) {
      setImage(res.assets[0]);
      setResult(null);
    }
  };

  const diagnose = async () => {
    if (!image) return;
    setLoading(true);
    try {
      const data = await predict(image.uri);
      setResult(data);
      // Save history
      const history = JSON.parse(await AsyncStorage.getItem('history') || '[]');
      history.unshift({ date: new Date().toISOString(), result: data, imageUri: image.uri });
      await AsyncStorage.setItem('history', JSON.stringify(history.slice(0, 30)));
    } catch (e) {
      Alert.alert('Lỗi', 'Không thể kết nối server. Kiểm tra mạng và thử lại.');
    } finally { setLoading(false); }
  };

  const reset = () => { setImage(null); setResult(null); };

  const p = result?.predictions?.[0];
  const isHealthy = p?.label?.toLowerCase().includes('healthy') || p?.label?.includes('Khỏe mạnh');

  return (
    <SafeAreaView style={s.container}>
      <ScrollView contentContainerStyle={s.scroll}>
        <View style={s.header}>
          <Text style={s.logo}>🌿</Text>
          <View>
            <Text style={s.title}>PlantDoctor</Text>
            <Text style={s.subtitle}>Chẩn đoán bệnh cây trồng bằng AI</Text>
          </View>
        </View>

        {!result ? (
          <>
            {image ? (
              <View style={{ position: 'relative' }}>
                <Image source={{ uri: image.uri }} style={s.preview} resizeMode="contain" />
                {loading && <ScanOverlay />}
              </View>
            ) : (
              <View style={s.placeholder}>
                <Text style={{ fontSize: 48 }}>📷</Text>
                <Text style={s.phText}>Chụp hoặc chọn ảnh lá cây để chẩn đoán</Text>
              </View>
            )}

            <TouchableOpacity style={s.btnCamera} onPress={() => pickImage(true)}>
              <Text style={s.btnCameraText}>📸 Chụp ảnh</Text>
            </TouchableOpacity>

            <TouchableOpacity style={s.btnOutline} onPress={() => pickImage(false)}>
              <Text style={s.btnOutlineText}>🖼️ Chọn từ thư viện</Text>
            </TouchableOpacity>

            <TouchableOpacity style={[s.btnPrimary, !image && s.btnDisabled]} onPress={diagnose} disabled={!image || loading}>
              {loading ? (
                <View style={s.loadingRow}>
                  <ActivityIndicator color="#fff" />
                  <Text style={s.btnPrimaryText}> Đang phân tích...</Text>
                </View>
              ) : <Text style={s.btnPrimaryText}>🔍 Chẩn đoán bệnh</Text>}
            </TouchableOpacity>
          </>
        ) : (
          <>
            {image && <Image source={{ uri: image.uri }} style={s.previewSmall} resizeMode="contain" />}

            <View style={[s.resultCard, isHealthy ? s.resultOk : s.resultBad]}>
              <Text style={s.resultName}>{p.name}</Text>
              {p.severity ? <Text style={s.severity}>Mức độ: {p.severity}</Text> : null}
              <View style={s.confBar}><View style={[s.confFill, { width: `${p.confidence}%`, backgroundColor: p.confidence >= 80 ? '#22c55e' : '#eab308' }]} /></View>
              <Text style={s.confText}>Độ tin cậy: {p.confidence}%</Text>
              {isHealthy && <Text style={s.healthyText}>✅ Cây khỏe mạnh!</Text>}
            </View>

            {p.description ? (
              <View style={s.section}>
                <Text style={s.secTitle}>🔍 Triệu chứng</Text>
                <Text style={s.secText}>{p.description}</Text>
              </View>
            ) : null}

            {p.treatment && !isHealthy ? (
              <View style={s.section}>
                <Text style={s.secTitle}>💊 Điều trị</Text>
                <Text style={s.secText}>{p.treatment}</Text>
              </View>
            ) : null}

            {p.medicines?.length > 0 && !isHealthy ? (
              <View style={s.section}>
                <Text style={s.secTitle}>🧪 Thuốc đề xuất</Text>
                {p.banned_warning?.length > 0 && (
                  <View style={{ backgroundColor: '#fef2f2', padding: 8, borderRadius: 8, marginBottom: 8 }}>
                    <Text style={{ color: '#dc2626', fontSize: 12, fontWeight: '700' }}>🚫 Cấm: {p.banned_warning.join(', ')}</Text>
                  </View>
                )}
                {p.matched_products?.map((mp, i) => (
                  <View key={i} style={{ backgroundColor: mp.banned ? '#fef2f2' : '#f0fdf4', padding: 10, borderRadius: 8, marginBottom: 6 }}>
                    <Text style={{ fontWeight: '700', color: mp.banned ? '#dc2626' : '#166534', fontSize: 13 }}>
                      {mp.banned ? '🚫' : '✅'} {mp.active}
                    </Text>
                    {mp.banned ? (
                      <Text style={{ color: '#dc2626', fontSize: 11 }}>Hoạt chất CẤM tại VN</Text>
                    ) : mp.products?.length > 0 ? (
                      mp.products.map((prod, j) => (
                        <Text key={j} style={{ fontSize: 12, color: '#444', marginTop: 2 }}>• {prod.name} - {prod.company}</Text>
                      ))
                    ) : (
                      <Text style={{ fontSize: 11, color: '#999' }}>Không tìm thấy trong danh mục VN</Text>
                    )}
                  </View>
                ))}
              </View>
            ) : null}

            <TouchableOpacity style={s.btnOutline} onPress={reset}>
              <Text style={s.btnOutlineText}>📷 Chẩn đoán ảnh khác</Text>
            </TouchableOpacity>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  scroll: { padding: 20, paddingBottom: 40 },
  header: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 20 },
  logo: { fontSize: 32 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#166534' },
  subtitle: { fontSize: 12, color: '#16a34a' },
  placeholder: { height: 200, backgroundColor: '#f0fdf4', borderRadius: 16, borderWidth: 2, borderColor: '#86efac', borderStyle: 'dashed', justifyContent: 'center', alignItems: 'center', marginBottom: 16 },
  phText: { color: '#16a34a', fontSize: 14, marginTop: 8, textAlign: 'center', paddingHorizontal: 20 },
  preview: { width: '100%', height: 250, borderRadius: 16, marginBottom: 16, backgroundColor: '#f9fafb' },
  previewSmall: { width: '100%', height: 150, borderRadius: 12, marginBottom: 12, backgroundColor: '#f9fafb' },
  btnCamera: { backgroundColor: '#166534', padding: 16, borderRadius: 14, alignItems: 'center', marginBottom: 10 },
  btnCameraText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  btnPrimary: { backgroundColor: '#16a34a', padding: 16, borderRadius: 14, alignItems: 'center', marginTop: 6 },
  btnPrimaryText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  btnDisabled: { opacity: 0.4 },
  btnOutline: { borderWidth: 2, borderColor: '#16a34a', padding: 14, borderRadius: 14, alignItems: 'center', marginBottom: 10 },
  btnOutlineText: { color: '#166534', fontSize: 15, fontWeight: '600' },
  loadingRow: { flexDirection: 'row', alignItems: 'center' },
  resultCard: { padding: 16, borderRadius: 14, marginBottom: 12 },
  resultOk: { backgroundColor: '#f0fdf4', borderWidth: 1, borderColor: '#86efac' },
  resultBad: { backgroundColor: '#fef2f2', borderWidth: 1, borderColor: '#fca5a5' },
  resultName: { fontSize: 18, fontWeight: 'bold', color: '#111', marginBottom: 6 },
  severity: { fontSize: 13, color: '#666', marginBottom: 8 },
  confBar: { height: 10, backgroundColor: '#e5e7eb', borderRadius: 5, marginBottom: 4 },
  confFill: { height: 10, borderRadius: 5 },
  confText: { fontSize: 12, color: '#666' },
  healthyText: { marginTop: 10, color: '#16a34a', fontWeight: '600', fontSize: 16 },
  section: { backgroundColor: '#f9fafb', padding: 14, borderRadius: 12, marginBottom: 10 },
  secTitle: { fontWeight: '700', color: '#111', marginBottom: 6, fontSize: 15 },
  secText: { fontSize: 14, color: '#444', lineHeight: 22 },
  medicine: { fontSize: 14, color: '#444', marginLeft: 8, marginTop: 3 },
});
