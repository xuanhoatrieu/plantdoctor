import { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  StyleSheet,
  Alert,
  Animated,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SafeAreaView } from 'react-native-safe-area-context';
import { predict, clarifyPrediction } from '../src/api';

const POPULAR_PLANTS = [
  { id: null, label: 'Tất cả cây', icon: '🌱' },
  { id: 'Cam/Bưởi', label: 'Cam/Bưởi', icon: '🍊' },
  { id: 'Lúa', label: 'Lúa', icon: '🌾' },
  { id: 'Chè', label: 'Chè', icon: '🍵' },
  { id: 'Cà phê', label: 'Cà phê', icon: '☕' },
  { id: 'Sầu riêng', label: 'Sầu riêng', icon: '🍈' },
  { id: 'Hồ tiêu/Ớt', label: 'Tiêu/Ớt', icon: '🌶️' },
  { id: 'Cà chua', label: 'Cà chua', icon: '🍅' },
  { id: 'Chuối', label: 'Chuối', icon: '🍌' },
  { id: 'Ngô', label: 'Ngô (Bắp)', icon: '🌽' },
];

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
  const translateY = anim.interpolate({ inputRange: [0, 1], outputRange: [0, 200] });
  return (
    <View style={StyleSheet.absoluteFill}>
      <View style={{ ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.35)', borderRadius: 16 }} />
      <Animated.View style={{ position: 'absolute', left: 0, right: 0, height: 3, backgroundColor: '#4ade80', borderRadius: 2, transform: [{ translateY }] }} />
    </View>
  );
}

export default function HomeScreen() {
  // Dual-image slots: image1 = Closeup/Lesion, image2 = Overview/Branch
  const [image1, setImage1] = useState(null);
  const [image2, setImage2] = useState(null);
  const [selectedPlant, setSelectedPlant] = useState(null);
  const [captureMode, setCaptureMode] = useState('leaf'); // 'leaf' | 'closeup' | 'stem'
  const [loading, setLoading] = useState(false);
  const [clarifying, setClarifying] = useState(false);
  const [result, setResult] = useState(null);
  const [feedbackGiven, setFeedbackGiven] = useState(null); // 'yes' | 'no'

  // Load saved plant filter on start
  useEffect(() => {
    AsyncStorage.getItem('last_selected_plant').then((val) => {
      if (val) setSelectedPlant(val);
    });
  }, []);

  const handleSelectPlant = (plantId) => {
    setSelectedPlant(plantId);
    if (plantId) {
      AsyncStorage.setItem('last_selected_plant', plantId);
    } else {
      AsyncStorage.removeItem('last_selected_plant');
    }
  };

  const pickImage = async (slotIndex, useCamera) => {
    if (useCamera) {
      const { status } = await ImagePicker.requestCameraPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Cần quyền camera', 'Vui lòng cấp quyền camera trong Cài đặt');
        return;
      }
    } else {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Cần quyền thư viện ảnh', 'Vui lòng cấp quyền trong Cài đặt');
        return;
      }
    }

    const method = useCamera ? ImagePicker.launchCameraAsync : ImagePicker.launchImageLibraryAsync;
    const res = await method({ mediaTypes: ['images'], quality: 0.8 });
    if (!res.canceled && res.assets?.[0]) {
      const asset = res.assets[0];
      if (slotIndex === 1) {
        setImage1(asset);
      } else {
        setImage2(asset);
      }
      setResult(null);
      setFeedbackGiven(null);
    }
  };

  const diagnose = async () => {
    if (!image1) {
      Alert.alert('Thiếu ảnh', 'Vui lòng chụp hoặc chọn ít nhất 1 ảnh vết bệnh');
      return;
    }

    setLoading(true);
    setResult(null);
    setFeedbackGiven(null);

    const imageUris = [image1.uri];
    if (image2) {
      imageUris.push(image2.uri);
    }

    try {
      const data = await predict(imageUris, 'vi', selectedPlant);
      setResult(data);

      // Save to history if diagnosis is complete
      if (data.status === 'success') {
        const history = JSON.parse((await AsyncStorage.getItem('history')) || '[]');
        history.unshift({
          date: new Date().toISOString(),
          result: data,
          imageUri: image1.uri,
          imageUri2: image2?.uri || null,
          plantHint: selectedPlant,
        });
        await AsyncStorage.setItem('history', JSON.stringify(history.slice(0, 30)));
      }
    } catch (e) {
      console.error('Diagnosis error:', e);
      let detail = e.message || 'Không thể kết nối máy chủ. Vui lòng kiểm tra mạng và thử lại.';
      if (e.code === 'ECONNABORTED' || e.message?.includes('timeout') || e.message?.includes('Quá thời gian')) {
        detail = 'Quá thời gian chờ phản hồi AI (hơn 120 giây). Vui lòng thử lại với ảnh rõ nét hơn.';
      } else if (e.response?.data?.detail) {
        detail = typeof e.response.data.detail === 'string' ? e.response.data.detail : JSON.stringify(e.response.data.detail);
      }
      Alert.alert('Lỗi chẩn đoán', detail);
    } finally {
      setLoading(false);
    }
  };

  const handleClarify = async (candidatePlantName) => {
    if (!result?.session_token) return;
    setClarifying(true);
    try {
      const clarifiedData = await clarifyPrediction(result.session_token, candidatePlantName, 'vi');
      setResult(clarifiedData);

      // Save resolved diagnosis to history
      const history = JSON.parse((await AsyncStorage.getItem('history')) || '[]');
      history.unshift({
        date: new Date().toISOString(),
        result: clarifiedData,
        imageUri: image1.uri,
        imageUri2: image2?.uri || null,
        plantHint: candidatePlantName,
      });
      await AsyncStorage.setItem('history', JSON.stringify(history.slice(0, 30)));
    } catch (e) {
      Alert.alert('Lỗi xác nhận', e.message || 'Không thể xác nhận loại cây');
    } finally {
      setClarifying(false);
    }
  };

  const handleFeedback = (isCorrect) => {
    setFeedbackGiven(isCorrect ? 'yes' : 'no');
    if (!isCorrect) {
      Alert.prompt
        ? Alert.prompt(
            'Phản hồi chẩn đoán',
            'Cây hoặc bệnh thực tế của bạn là gì để chúng tôi cải thiện AI?',
            [
              { text: 'Bỏ qua', style: 'cancel' },
              { text: 'Gửi', onPress: () => Alert.alert('Cảm ơn', 'Đã ghi nhận ý kiến đóng góp của bạn!') },
            ]
          )
        : Alert.alert('Cảm ơn', 'Đã ghi nhận phản hồi để hoàn thiện mô hình AI!');
    } else {
      Alert.alert('Cảm ơn', 'Phản hồi tích cực của bạn giúp AI ngày càng chuẩn xác hơn!');
    }
  };

  const reset = () => {
    setImage1(null);
    setImage2(null);
    setResult(null);
    setFeedbackGiven(null);
  };

  const qualityWarnings = result?.image_quality_warnings || [];
  const votingUsed = result?.voting_used || false;
  const isCached = result?.cached || false;
  const isClarification = result?.status === 'needs_clarification';

  const p = result?.predictions?.[0];
  const isHealthy = p?.label?.toLowerCase().includes('healthy') || p?.label?.includes('Khỏe mạnh');
  const hasQualityWarnings = qualityWarnings.length > 0;

  return (
    <SafeAreaView style={s.container}>
      <ScrollView contentContainerStyle={s.scroll}>
        {/* Header */}
        <View style={s.header}>
          <Text style={s.logo}>🌿</Text>
          <View>
            <Text style={s.title}>PlantDoctor</Text>
            <Text style={s.subtitle}>Chẩn đoán bệnh cây trồng bằng AI</Text>
          </View>
        </View>

        <View style={{ alignItems: 'center', marginBottom: 12 }}>
          <Text style={{ fontSize: 15, fontWeight: 'bold', color: '#166534' }}>
            Trường Đại học Nông Lâm Thái Nguyên
          </Text>
          <Text style={{ fontSize: 11, color: '#16a34a' }}>Cùng bạn ra thế giới!</Text>
        </View>

        {/* Phase 1.3: Plant Selector Chips */}
        <View style={{ marginBottom: 14 }}>
          <Text style={{ fontSize: 13, fontWeight: '600', color: '#374151', marginBottom: 6 }}>
            🌾 Chọn loại cây trồng (Tùy chọn — giúp AI chẩn đoán cực nhanh):
          </Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8, paddingVertical: 2 }}>
            {POPULAR_PLANTS.map((item) => {
              const isSelected = selectedPlant === item.id;
              return (
                <TouchableOpacity
                  key={String(item.id)}
                  style={[s.plantChip, isSelected && s.plantChipActive]}
                  onPress={() => handleSelectPlant(item.id)}
                >
                  <Text style={{ fontSize: 14 }}>{item.icon}</Text>
                  <Text style={[s.plantChipText, isSelected && s.plantChipTextActive]}>{item.label}</Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>

        {!result || isClarification ? (
          <>
            {/* Phase 2.1: Mode Switcher & Smart Viewfinder Tips */}
            <View style={s.modeContainer}>
              <TouchableOpacity
                style={[s.modeBtn, captureMode === 'leaf' && s.modeBtnActive]}
                onPress={() => setCaptureMode('leaf')}
              >
                <Text style={[s.modeText, captureMode === 'leaf' && s.modeTextActive]}>🍃 Lá cây</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[s.modeBtn, captureMode === 'closeup' && s.modeBtnActive]}
                onPress={() => setCaptureMode('closeup')}
              >
                <Text style={[s.modeText, captureMode === 'closeup' && s.modeTextActive]}>🔍 Vết bệnh cận cảnh</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[s.modeBtn, captureMode === 'stem' && s.modeBtnActive]}
                onPress={() => setCaptureMode('stem')}
              >
                <Text style={[s.modeText, captureMode === 'stem' && s.modeTextActive]}>🪵 Thân / Cành</Text>
              </TouchableOpacity>
            </View>

            {/* Smart Tip Banner */}
            <View style={s.tipCard}>
              <Text style={s.tipTitle}>
                {captureMode === 'leaf' && '💡 Mẹo chụp lá cây chuẩn xác:'}
                {captureMode === 'closeup' && '💡 Mẹo chụp cận cảnh vết bệnh:'}
                {captureMode === 'stem' && '💡 Mẹo chụp thân và vỏ cây:'}
              </Text>
              <Text style={s.tipContent}>
                {captureMode === 'leaf' && 'Đặt trọn vẹn cả phiến lá và cuống lá vào khung hình, chụp đủ ánh sáng, tránh che tay.'}
                {captureMode === 'closeup' && 'Nên chụp thêm 1 ảnh toàn cảnh cành lá ở Khung 2 để AI nhận diện đúng cây, không bị nhầm lẫn.'}
                {captureMode === 'stem' && 'Chụp rõ vết loét/xì mủ. Nếu có cành lá kèm theo, hãy chụp thêm ở Khung 2.'}
              </Text>
            </View>

            {/* Phase 1.4: Dual Image Slots */}
            <View style={s.slotsRow}>
              {/* Slot 1: Close-up / Lesion (Required) */}
              <View style={[s.slotBox, image1 && s.slotBoxActive]}>
                <View style={s.slotHeader}>
                  <Text style={s.slotBadge}>Ảnh 1: Vết bệnh (*)</Text>
                  {image1 && (
                    <TouchableOpacity onPress={() => setImage1(null)}>
                      <Text style={{ color: '#ef4444', fontSize: 12, fontWeight: '700' }}>Xóa</Text>
                    </TouchableOpacity>
                  )}
                </View>

                {image1 ? (
                  <View style={{ position: 'relative', width: '100%', height: 160, borderRadius: 10, overflow: 'hidden' }}>
                    <Image source={{ uri: image1.uri }} style={{ width: '100%', height: '100%' }} resizeMode="cover" />
                    {loading && <ScanOverlay />}
                  </View>
                ) : (
                  <View style={s.slotEmpty}>
                    <Text style={{ fontSize: 32 }}>📸</Text>
                    <Text style={s.slotEmptyText}>Ảnh cận cảnh vết bệnh</Text>
                    <View style={s.slotBtnRow}>
                      <TouchableOpacity style={s.miniBtn} onPress={() => pickImage(1, true)}>
                        <Text style={s.miniBtnText}>Chụp</Text>
                      </TouchableOpacity>
                      <TouchableOpacity style={s.miniBtnOutline} onPress={() => pickImage(1, false)}>
                        <Text style={s.miniBtnOutlineText}>Thư viện</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                )}
              </View>

              {/* Slot 2: Overview / Branch (Optional / Recommended) */}
              <View style={[s.slotBox, image2 && s.slotBoxActive]}>
                <View style={s.slotHeader}>
                  <Text style={[s.slotBadge, { backgroundColor: '#f0fdf4', color: '#166534' }]}>Ảnh 2: Toàn cành lá</Text>
                  {image2 && (
                    <TouchableOpacity onPress={() => setImage2(null)}>
                      <Text style={{ color: '#ef4444', fontSize: 12, fontWeight: '700' }}>Xóa</Text>
                    </TouchableOpacity>
                  )}
                </View>

                {image2 ? (
                  <View style={{ position: 'relative', width: '100%', height: 160, borderRadius: 10, overflow: 'hidden' }}>
                    <Image source={{ uri: image2.uri }} style={{ width: '100%', height: '100%' }} resizeMode="cover" />
                    {loading && <ScanOverlay />}
                  </View>
                ) : (
                  <View style={s.slotEmpty}>
                    <Text style={{ fontSize: 32 }}>🌿</Text>
                    <Text style={s.slotEmptyText}>Ảnh toàn cảnh cành/cây</Text>
                    <View style={s.slotBtnRow}>
                      <TouchableOpacity style={s.miniBtn} onPress={() => pickImage(2, true)}>
                        <Text style={s.miniBtnText}>Chụp</Text>
                      </TouchableOpacity>
                      <TouchableOpacity style={s.miniBtnOutline} onPress={() => pickImage(2, false)}>
                        <Text style={s.miniBtnOutlineText}>Thư viện</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                )}
              </View>
            </View>

            {/* Phase 2.2: Interactive Clarification Sheet (When AI needs more context) */}
            {isClarification && (
              <View style={s.clarifyBox}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <Text style={{ fontSize: 24 }}>🤖</Text>
                  <Text style={{ fontSize: 15, fontWeight: 'bold', color: '#1e3a8a', flex: 1 }}>
                    Trợ lý PlantDoctor cần bạn hỗ trợ:
                  </Text>
                </View>

                <Text style={{ fontSize: 13, color: '#1e40af', lineHeight: 20, marginBottom: 10 }}>
                  {result.clarification_message}
                </Text>

                {result.preliminary_symptoms ? (
                  <View style={{ backgroundColor: '#fff', padding: 8, borderRadius: 8, marginBottom: 12, borderWidth: 1, borderColor: '#bfdbfe' }}>
                    <Text style={{ fontSize: 12, color: '#475569' }}>
                      <Text style={{ fontWeight: '700' }}>🔍 Dấu hiệu quan sát:</Text> {result.preliminary_symptoms}
                    </Text>
                  </View>
                ) : null}

                <Text style={{ fontSize: 12, fontWeight: '700', color: '#1e3a8a', marginBottom: 8 }}>
                  Bấm chọn loại cây của bạn:
                </Text>

                <View style={{ gap: 8 }}>
                  {result.candidate_plants?.map((cand) => (
                    <TouchableOpacity
                      key={cand.id}
                      style={s.candBtn}
                      onPress={() => handleClarify(cand.name)}
                      disabled={clarifying}
                    >
                      <Text style={{ fontSize: 18 }}>{cand.icon}</Text>
                      <Text style={s.candBtnText}>{cand.name}</Text>
                    </TouchableOpacity>
                  ))}
                </View>

                {clarifying && (
                  <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginTop: 12, gap: 8 }}>
                    <ActivityIndicator color="#1e40af" />
                    <Text style={{ fontSize: 13, color: '#1e40af', fontWeight: '600' }}>Đang hoàn tất kết luận...</Text>
                  </View>
                )}

                <TouchableOpacity
                  style={{ marginTop: 14, padding: 10, alignItems: 'center', backgroundColor: '#e0e7ff', borderRadius: 10 }}
                  onPress={() => pickImage(2, true)}
                >
                  <Text style={{ color: '#3730a3', fontSize: 13, fontWeight: '700' }}>
                    📸 Hoặc chụp thêm 1 ảnh cành lá vào Khung 2
                  </Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Diagnose Button */}
            {!isClarification && (
              <TouchableOpacity
                style={[s.btnPrimary, !image1 && s.btnDisabled]}
                onPress={diagnose}
                disabled={!image1 || loading}
              >
                {loading ? (
                  <View style={s.loadingRow}>
                    <ActivityIndicator color="#fff" />
                    <Text style={s.btnPrimaryText}> Đang phân tích kết hợp...</Text>
                  </View>
                ) : (
                  <Text style={s.btnPrimaryText}>🔍 Chẩn đoán bệnh bằng AI</Text>
                )}
              </TouchableOpacity>
            )}

            <View style={s.noteBox}>
              <Text style={s.noteText}>
                💡 Gợi ý: Gửi cùng lúc 2 ảnh (ảnh 1 vết bệnh + ảnh 2 cành lá) giúp AI đạt độ chính xác cao nhất (trên 95%).
              </Text>
            </View>
          </>
        ) : (
          /* RESULT VIEW */
          <>
            {/* Display uploaded images thumbnails */}
            <View style={{ flexDirection: 'row', gap: 10, marginBottom: 12 }}>
              {image1 && (
                <View style={{ flex: 1, position: 'relative' }}>
                  <Image source={{ uri: image1.uri }} style={s.previewSmall} resizeMode="cover" />
                  <View style={s.thumbTag}><Text style={s.thumbTagText}>Vết bệnh</Text></View>
                </View>
              )}
              {image2 && (
                <View style={{ flex: 1, position: 'relative' }}>
                  <Image source={{ uri: image2.uri }} style={s.previewSmall} resizeMode="cover" />
                  <View style={s.thumbTag}><Text style={s.thumbTagText}>Toàn cây</Text></View>
                </View>
              )}
            </View>

            {/* Quality warnings */}
            {hasQualityWarnings && (
              <View style={s.warningCard}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                  <Text style={{ fontSize: 16 }}>📸</Text>
                  <Text style={{ fontSize: 13, fontWeight: '700', color: '#9a3412' }}>Gợi ý cải thiện ảnh:</Text>
                </View>
                {qualityWarnings.map((w, i) => (
                  <Text key={i} style={s.warningItem}>• {w}</Text>
                ))}
              </View>
            )}

            {/* Voting / Cache badges */}
            {votingUsed && (
              <View style={s.badgeRow}>
                <Text>🔄</Text>
                <Text style={s.badgeText}>Kết quả đã được xác nhận qua AI voting (3 lần phân tích)</Text>
              </View>
            )}

            {isCached && (
              <View style={[s.badgeRow, { backgroundColor: '#f0fdf4', borderColor: '#86efac' }]}>
                <Text>⚡</Text>
                <Text style={[s.badgeText, { color: '#166534' }]}>Kết quả từ bộ nhớ đệm (nhất quán 100%)</Text>
              </View>
            )}

            {/* Main Result Card */}
            <View style={[s.resultCard, isHealthy ? s.resultOk : s.resultBad]}>
              <Text style={s.resultName}>{p.name}</Text>
              {p.severity ? <Text style={s.severity}>Mức độ: {p.severity}</Text> : null}
              <View style={s.confBar}>
                <View
                  style={[
                    s.confFill,
                    {
                      width: `${p.confidence}%`,
                      backgroundColor: p.confidence >= 80 ? '#22c55e' : '#eab308',
                    },
                  ]}
                />
              </View>
              <Text style={s.confText}>Độ tin cậy: {p.confidence}%</Text>
              {isHealthy && <Text style={s.healthyText}>✅ Cây khỏe mạnh!</Text>}
            </View>

            {/* Symptoms */}
            {p.description ? (
              <View style={s.section}>
                <Text style={s.secTitle}>🔍 Triệu chứng quan sát được</Text>
                <Text style={s.secText}>{p.description}</Text>
              </View>
            ) : null}

            {/* Treatment */}
            {p.treatment && !isHealthy ? (
              <View style={s.section}>
                <Text style={s.secTitle}>💊 Biện pháp điều trị & kỹ thuật</Text>
                <Text style={s.secText}>{p.treatment}</Text>
              </View>
            ) : null}

            {/* Pesticides */}
            {p.medicines?.length > 0 && !isHealthy ? (
              <View style={s.section}>
                <Text style={s.secTitle}>🧪 Thuốc bảo vệ thực vật đề xuất</Text>
                {p.banned_warning?.length > 0 && (
                  <View style={s.bannedBox}>
                    <Text style={s.bannedText}>🚫 Cấm tại VN: {p.banned_warning.join(', ')}</Text>
                  </View>
                )}
                {p.matched_products?.map((mp, i) => (
                  <View key={i} style={[s.medCard, mp.banned ? s.medBanned : s.medOk]}>
                    <Text style={[s.medActive, { color: mp.banned ? '#dc2626' : '#166534' }]}>
                      {mp.banned ? '🚫' : '✅'} {mp.active}
                    </Text>
                    {mp.banned ? (
                      <Text style={{ color: '#dc2626', fontSize: 11 }}>Hoạt chất CẤM tại Việt Nam</Text>
                    ) : mp.products?.length > 0 ? (
                      mp.products.map((prod, j) => (
                        <Text key={j} style={s.medProd}>• {prod.name} - {prod.company}</Text>
                      ))
                    ) : (
                      <Text style={{ fontSize: 11, color: '#999' }}>Chưa cập nhật tên thương phẩm</Text>
                    )}
                  </View>
                ))}
              </View>
            ) : null}

            {/* Phase 3.3: User Feedback Loop */}
            <View style={s.feedbackCard}>
              <Text style={s.feedbackTitle}>Chẩn đoán này có chuẩn xác không?</Text>
              <View style={s.feedbackRow}>
                <TouchableOpacity
                  style={[s.feedbackBtn, feedbackGiven === 'yes' && s.feedbackBtnActive]}
                  onPress={() => handleFeedback(true)}
                >
                  <Text style={s.feedbackBtnText}>👍 Chuẩn xác</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[s.feedbackBtn, feedbackGiven === 'no' && s.feedbackBtnNoActive]}
                  onPress={() => handleFeedback(false)}
                >
                  <Text style={s.feedbackBtnText}>👎 Chưa đúng</Text>
                </TouchableOpacity>
              </View>
            </View>

            <TouchableOpacity style={s.btnOutline} onPress={reset}>
              <Text style={s.btnOutlineText}>📷 Chẩn đoán cây khác</Text>
            </TouchableOpacity>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  scroll: { padding: 16, paddingBottom: 40 },
  header: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 12 },
  logo: { fontSize: 30 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#166534' },
  subtitle: { fontSize: 12, color: '#16a34a' },

  // Plant Selector Chips
  plantChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 20,
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#d1d5db',
  },
  plantChipActive: {
    backgroundColor: '#166534',
    borderColor: '#166534',
  },
  plantChipText: { fontSize: 12, fontWeight: '600', color: '#4b5563' },
  plantChipTextActive: { color: '#ffffff' },

  // Mode Switcher
  modeContainer: {
    flexDirection: 'row',
    backgroundColor: '#e2e8f0',
    borderRadius: 12,
    padding: 3,
    marginBottom: 10,
  },
  modeBtn: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 9,
  },
  modeBtnActive: {
    backgroundColor: '#ffffff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  modeText: { fontSize: 12, fontWeight: '600', color: '#64748b' },
  modeTextActive: { color: '#166534', fontWeight: '700' },

  // Tip Card
  tipCard: {
    backgroundColor: '#f0fdf4',
    borderLeftWidth: 3,
    borderLeftColor: '#22c55e',
    padding: 10,
    borderRadius: 8,
    marginBottom: 14,
  },
  tipTitle: { fontSize: 12, fontWeight: '700', color: '#166534', marginBottom: 2 },
  tipContent: { fontSize: 12, color: '#15803d', lineHeight: 17 },

  // Dual Slots
  slotsRow: { flexDirection: 'row', gap: 10, marginBottom: 14 },
  slotBox: {
    flex: 1,
    backgroundColor: '#ffffff',
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#cbd5e1',
    borderStyle: 'dashed',
    padding: 8,
    minHeight: 180,
  },
  slotBoxActive: {
    borderStyle: 'solid',
    borderColor: '#86efac',
    backgroundColor: '#f8fafc',
  },
  slotHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  slotBadge: {
    fontSize: 11,
    fontWeight: '700',
    color: '#0f766e',
    backgroundColor: '#ccfbf1',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  slotEmpty: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 12,
  },
  slotEmptyText: { fontSize: 11, color: '#64748b', textAlign: 'center', marginTop: 4, marginBottom: 8 },
  slotBtnRow: { flexDirection: 'row', gap: 6 },
  miniBtn: {
    backgroundColor: '#166534',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  miniBtnText: { color: '#ffffff', fontSize: 11, fontWeight: '600' },
  miniBtnOutline: {
    borderWidth: 1,
    borderColor: '#166534',
    paddingHorizontal: 8,
    paddingVertical: 6,
    borderRadius: 8,
  },
  miniBtnOutlineText: { color: '#166534', fontSize: 11, fontWeight: '600' },

  // Clarification Box
  clarifyBox: {
    backgroundColor: '#eff6ff',
    borderWidth: 1.5,
    borderColor: '#93c5fd',
    borderRadius: 14,
    padding: 14,
    marginBottom: 14,
  },
  candBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#ffffff',
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#bfdbfe',
  },
  candBtnText: { fontSize: 13, fontWeight: '700', color: '#1e3a8a' },

  // Buttons
  btnPrimary: {
    backgroundColor: '#166534',
    padding: 16,
    borderRadius: 14,
    alignItems: 'center',
    marginTop: 4,
    shadowColor: '#166534',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.25,
    shadowRadius: 5,
    elevation: 3,
  },
  btnPrimaryText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  btnDisabled: { opacity: 0.45 },
  btnOutline: {
    borderWidth: 2,
    borderColor: '#166534',
    padding: 14,
    borderRadius: 14,
    alignItems: 'center',
    marginTop: 10,
    marginBottom: 10,
    backgroundColor: '#ffffff',
  },
  btnOutlineText: { color: '#166534', fontSize: 15, fontWeight: '600' },
  loadingRow: { flexDirection: 'row', alignItems: 'center' },

  noteBox: {
    backgroundColor: '#f1f5f9',
    borderRadius: 10,
    padding: 10,
    marginTop: 12,
  },
  noteText: { fontSize: 11, color: '#475569', textAlign: 'center', lineHeight: 16 },

  // Result Cards
  previewSmall: { width: '100%', height: 120, borderRadius: 10, backgroundColor: '#f1f5f9' },
  thumbTag: {
    position: 'absolute',
    bottom: 4,
    left: 4,
    backgroundColor: 'rgba(0,0,0,0.65)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  thumbTagText: { color: '#fff', fontSize: 10, fontWeight: '600' },

  warningCard: {
    backgroundColor: '#fff7ed',
    borderWidth: 1,
    borderColor: '#fdba74',
    borderRadius: 10,
    padding: 12,
    marginBottom: 10,
  },
  warningItem: { fontSize: 12, color: '#c2410c', marginLeft: 22, marginTop: 2, lineHeight: 17 },

  badgeRow: {
    backgroundColor: '#eff6ff',
    borderWidth: 1,
    borderColor: '#93c5fd',
    borderRadius: 8,
    padding: 8,
    marginBottom: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  badgeText: { fontSize: 11, color: '#1e40af', flex: 1 },

  resultCard: { padding: 16, borderRadius: 14, marginBottom: 12 },
  resultOk: { backgroundColor: '#f0fdf4', borderWidth: 1, borderColor: '#86efac' },
  resultBad: { backgroundColor: '#fef2f2', borderWidth: 1, borderColor: '#fca5a5' },
  resultName: { fontSize: 19, fontWeight: 'bold', color: '#111827', marginBottom: 4 },
  severity: { fontSize: 13, color: '#4b5563', marginBottom: 8 },
  confBar: { height: 8, backgroundColor: '#e2e8f0', borderRadius: 4, marginBottom: 4 },
  confFill: { height: 8, borderRadius: 4 },
  confText: { fontSize: 12, color: '#64748b' },
  healthyText: { marginTop: 8, color: '#16a34a', fontWeight: '700', fontSize: 15 },

  section: { backgroundColor: '#ffffff', padding: 14, borderRadius: 12, marginBottom: 10, borderWidth: 1, borderColor: '#e2e8f0' },
  secTitle: { fontWeight: '700', color: '#0f172a', marginBottom: 6, fontSize: 14 },
  secText: { fontSize: 13, color: '#334155', lineHeight: 20 },

  bannedBox: { backgroundColor: '#fef2f2', padding: 8, borderRadius: 8, marginBottom: 8 },
  bannedText: { color: '#dc2626', fontSize: 12, fontWeight: '700' },
  medCard: { padding: 10, borderRadius: 8, marginBottom: 6 },
  medOk: { backgroundColor: '#f0fdf4' },
  medBanned: { backgroundColor: '#fef2f2' },
  medActive: { fontWeight: '700', fontSize: 13 },
  medProd: { fontSize: 12, color: '#334155', marginTop: 2 },

  // Feedback Card
  feedbackCard: {
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 12,
    padding: 12,
    marginBottom: 10,
    alignItems: 'center',
  },
  feedbackTitle: { fontSize: 13, fontWeight: '600', color: '#334155', marginBottom: 8 },
  feedbackRow: { flexDirection: 'row', gap: 12 },
  feedbackBtn: {
    borderWidth: 1,
    borderColor: '#cbd5e1',
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 8,
    backgroundColor: '#f8fafc',
  },
  feedbackBtnActive: { backgroundColor: '#dcfce7', borderColor: '#86efac' },
  feedbackBtnNoActive: { backgroundColor: '#fee2e2', borderColor: '#fca5a5' },
  feedbackBtnText: { fontSize: 12, fontWeight: '600', color: '#334155' },
});
