// Full-screen camera with a framing guide that depends on what the farmer is photographing.
//   leaf    -> leaf silhouette (whole leaf blade + petiole inside the frame)
//   closeup -> circle (one lesion, filling the circle)
//   stem    -> tall rounded rectangle (a section of trunk / branch)
// The guide is only for framing: the saved photo is the full camera frame, so the AI still sees context.
// Uses expo-camera (already a dependency + config plugin in app.json); no new packages.
import { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Linking,
  Modal,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  useWindowDimensions,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { SafeAreaView } from 'react-native-safe-area-context';

export const CAPTURE_MODES = [
  { id: 'leaf', label: '🍃 Lá cây' },
  { id: 'closeup', label: '🔍 Cận vết bệnh' },
  { id: 'stem', label: '🪵 Thân / Cành' },
];

const TIPS = {
  leaf: 'Đặt trọn phiến lá và cuống lá vào khung hình chiếc lá. Chụp nơi đủ sáng, không để tay che vết bệnh.',
  closeup: 'Đưa 1 vết bệnh vào giữa vòng tròn, cách 10–20 cm. Chạm màn hình để lấy nét nếu ảnh bị mờ.',
  stem: 'Đặt đoạn thân/cành có vết loét, xì mủ dọc theo khung. Chụp thẳng góc, đủ sáng.',
  overview: 'Lùi ra 0,5–1 m để thấy cả cành, nhiều lá (và quả/hoa nếu có). Ảnh này giúp AI nhận đúng loại cây.',
};

const SLOT_TITLES = {
  1: 'Ảnh 1 · Vết bệnh',
  2: 'Ảnh 2 · Toàn cảnh cành/cây',
};

// Target rectangle (in screen coordinates) for each mode, kept above the bottom controls.
function computeFrame(mode, width, height) {
  const usableTop = 110;
  const usableBottom = height - 230;
  const usableH = Math.max(200, usableBottom - usableTop);
  let w;
  let h;
  if (mode === 'closeup') {
    w = h = Math.min(width * 0.7, usableH * 0.8);
  } else if (mode === 'stem') {
    h = usableH * 0.88;
    w = Math.min(width * 0.46, h * 0.42);
  } else if (mode === 'overview') {
    w = width * 0.88;
    h = Math.min(usableH * 0.9, w * 1.25);
  } else {
    w = Math.min(width * 0.78, usableH * 0.72);
    h = Math.min(usableH * 0.92, w * 1.3);
  }
  const x = (width - w) / 2;
  const y = usableTop + (usableH - h) / 2;
  return { x, y, w, h };
}

function CornerBrackets({ frame, color }) {
  const L = 26;
  const T = 4;
  const base = { position: 'absolute', width: L, height: L, borderColor: color };
  return (
    <>
      <View style={[base, { left: frame.x - 6, top: frame.y - 6, borderLeftWidth: T, borderTopWidth: T, borderTopLeftRadius: 8 }]} />
      <View style={[base, { left: frame.x + frame.w - L + 6, top: frame.y - 6, borderRightWidth: T, borderTopWidth: T, borderTopRightRadius: 8 }]} />
      <View style={[base, { left: frame.x - 6, top: frame.y + frame.h - L + 6, borderLeftWidth: T, borderBottomWidth: T, borderBottomLeftRadius: 8 }]} />
      <View style={[base, { left: frame.x + frame.w - L + 6, top: frame.y + frame.h - L + 6, borderRightWidth: T, borderBottomWidth: T, borderBottomRightRadius: 8 }]} />
    </>
  );
}

// Leaf silhouette: a square with two opposite corners fully rounded, rotated 45° so the
// pointed ends become the leaf tip (top) and the base (bottom), plus a midrib and a petiole.
function LeafGuide({ frame }) {
  const side = Math.min(frame.w, frame.h * 0.82) / Math.SQRT2;
  const cx = frame.x + frame.w / 2;
  const cy = frame.y + frame.h * 0.44;
  const bladeHalf = (side * Math.SQRT2) / 2;
  return (
    <>
      <View
        style={{
          position: 'absolute',
          width: side,
          height: side,
          left: cx - side / 2,
          top: cy - side / 2,
          borderWidth: 2.5,
          borderColor: 'rgba(255,255,255,0.95)',
          borderTopLeftRadius: side * 0.5,
          borderBottomRightRadius: side * 0.5,
          borderTopRightRadius: 4,
          borderBottomLeftRadius: 4,
          transform: [{ rotate: '-45deg' }],
          backgroundColor: 'rgba(74,222,128,0.08)',
        }}
      />
      {/* midrib */}
      <View style={{ position: 'absolute', width: 1.5, height: bladeHalf * 1.7, left: cx - 0.75, top: cy - bladeHalf * 0.85, backgroundColor: 'rgba(255,255,255,0.55)' }} />
      {/* petiole */}
      <View style={{ position: 'absolute', width: 3, height: frame.h * 0.1, left: cx - 1.5, top: cy + bladeHalf - 2, backgroundColor: 'rgba(255,255,255,0.9)', borderRadius: 2 }} />
    </>
  );
}

function CircleGuide({ frame }) {
  const d = Math.min(frame.w, frame.h);
  const cx = frame.x + frame.w / 2;
  const cy = frame.y + frame.h / 2;
  return (
    <>
      <View style={{ position: 'absolute', width: d, height: d, left: cx - d / 2, top: cy - d / 2, borderRadius: d / 2, borderWidth: 2.5, borderColor: 'rgba(255,255,255,0.95)', backgroundColor: 'rgba(74,222,128,0.06)' }} />
      <View style={{ position: 'absolute', width: 22, height: 2, left: cx - 11, top: cy - 1, backgroundColor: '#4ade80' }} />
      <View style={{ position: 'absolute', width: 2, height: 22, left: cx - 1, top: cy - 11, backgroundColor: '#4ade80' }} />
    </>
  );
}

function StemGuide({ frame }) {
  return (
    <>
      <View style={{ position: 'absolute', left: frame.x, top: frame.y, width: frame.w, height: frame.h, borderRadius: frame.w / 2.5, borderWidth: 2.5, borderColor: 'rgba(255,255,255,0.95)', backgroundColor: 'rgba(74,222,128,0.06)' }} />
      {[0.33, 0.66].map((f) => (
        <View key={f} style={{ position: 'absolute', left: frame.x + frame.w * f, top: frame.y + 16, width: 1, height: frame.h - 32, backgroundColor: 'rgba(255,255,255,0.35)' }} />
      ))}
    </>
  );
}

// Overview (photo 2): wide frame with a rule-of-thirds grid, the whole branch should fill it.
function OverviewGuide({ frame }) {
  const line = 'rgba(255,255,255,0.3)';
  return (
    <>
      <View style={{ position: 'absolute', left: frame.x, top: frame.y, width: frame.w, height: frame.h, borderRadius: 14, borderWidth: 2, borderColor: 'rgba(255,255,255,0.9)' }} />
      {[1 / 3, 2 / 3].map((f) => (
        <View key={`v${f}`} style={{ position: 'absolute', left: frame.x + frame.w * f, top: frame.y, width: 1, height: frame.h, backgroundColor: line }} />
      ))}
      {[1 / 3, 2 / 3].map((f) => (
        <View key={`h${f}`} style={{ position: 'absolute', left: frame.x, top: frame.y + frame.h * f, width: frame.w, height: 1, backgroundColor: line }} />
      ))}
    </>
  );
}

// Darken everything outside the target rectangle (4 bands) so the eye goes to the frame.
function Mask({ frame, width, height }) {
  const c = 'rgba(0,0,0,0.5)';
  return (
    <>
      <View style={{ position: 'absolute', left: 0, top: 0, width, height: frame.y, backgroundColor: c }} />
      <View style={{ position: 'absolute', left: 0, top: frame.y + frame.h, width, height: Math.max(0, height - frame.y - frame.h), backgroundColor: c }} />
      <View style={{ position: 'absolute', left: 0, top: frame.y, width: frame.x, height: frame.h, backgroundColor: c }} />
      <View style={{ position: 'absolute', left: frame.x + frame.w, top: frame.y, width: Math.max(0, width - frame.x - frame.w), height: frame.h, backgroundColor: c }} />
    </>
  );
}

export default function SmartCamera({ visible, slot = 1, mode = 'leaf', onModeChange, onClose, onCapture }) {
  const { width, height } = useWindowDimensions();
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef(null);
  const [ready, setReady] = useState(false);
  const [torch, setTorch] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (visible) {
      setReady(false);
      setBusy(false);
      setError('');
      setTorch(false);
    }
  }, [visible]);

  const frame = computeFrame(mode, width, height);

  const shoot = async () => {
    if (!cameraRef.current || !ready || busy) return;
    setBusy(true);
    setError('');
    try {
      const photo = await cameraRef.current.takePictureAsync({ quality: 0.85 });
      if (!photo?.uri) throw new Error('no photo');
      setTorch(false);
      onCapture({ uri: photo.uri, width: photo.width, height: photo.height, fromCamera: true, mode });
    } catch {
      setError('Không chụp được ảnh. Vui lòng thử lại.');
    } finally {
      setBusy(false);
    }
  };

  const renderPermission = () => (
    <SafeAreaView style={st.permWrap}>
      <Text style={{ fontSize: 48, marginBottom: 12 }}>📷</Text>
      <Text style={st.permTitle}>PlantDoctor cần quyền dùng camera</Text>
      <Text style={st.permText}>Camera chỉ dùng để chụp ảnh cây trồng gửi đi chẩn đoán.</Text>
      {permission && !permission.canAskAgain ? (
        <TouchableOpacity style={st.permBtn} onPress={() => Linking.openSettings()}>
          <Text style={st.permBtnText}>Mở Cài đặt để cấp quyền</Text>
        </TouchableOpacity>
      ) : (
        <TouchableOpacity style={st.permBtn} onPress={requestPermission}>
          <Text style={st.permBtnText}>Cho phép dùng camera</Text>
        </TouchableOpacity>
      )}
      <TouchableOpacity style={{ marginTop: 14, padding: 10 }} onPress={onClose}>
        <Text style={{ color: '#cbd5e1', fontSize: 14 }}>Để sau</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose} statusBarTranslucent>
      <View style={st.root}>
        {!permission ? (
          <View style={st.permWrap}><ActivityIndicator color="#fff" /></View>
        ) : !permission.granted ? (
          renderPermission()
        ) : (
          <>
            <CameraView
              ref={cameraRef}
              style={StyleSheet.absoluteFill}
              facing="back"
              enableTorch={torch}
              onCameraReady={() => setReady(true)}
              onMountError={() => setError('Không mở được camera. Hãy đóng và thử lại, hoặc chọn ảnh từ Thư viện.')}
            />

            <View style={StyleSheet.absoluteFill} pointerEvents="none">
              <Mask frame={frame} width={width} height={height} />
              {mode === 'leaf' && <LeafGuide frame={frame} />}
              {mode === 'closeup' && <CircleGuide frame={frame} />}
              {mode === 'stem' && <StemGuide frame={frame} />}
              {mode === 'overview' && <OverviewGuide frame={frame} />}
              <CornerBrackets frame={frame} color="#4ade80" />
            </View>

            {/* Top bar */}
            <SafeAreaView style={st.topBar} edges={['top']}>
              <TouchableOpacity style={st.iconBtn} onPress={onClose} accessibilityLabel="Đóng camera">
                <Text style={st.iconText}>✕</Text>
              </TouchableOpacity>
              <Text style={st.topTitle}>{SLOT_TITLES[slot] || SLOT_TITLES[1]}</Text>
              <TouchableOpacity style={[st.iconBtn, torch && st.iconBtnOn]} onPress={() => setTorch((v) => !v)} accessibilityLabel="Bật/tắt đèn">
                <Text style={st.iconText}>{torch ? '🔦' : '💡'}</Text>
              </TouchableOpacity>
            </SafeAreaView>

            {/* Bottom controls */}
            <SafeAreaView style={st.bottom} edges={['bottom']}>
              <Text style={st.tip}>{TIPS[mode]}</Text>
              {error ? <Text style={st.error}>{error}</Text> : null}
              {mode !== 'overview' && (
                <View style={st.modeRow}>
                  {CAPTURE_MODES.map((m) => (
                    <TouchableOpacity key={m.id} onPress={() => onModeChange && onModeChange(m.id)}
                      style={[st.modePill, mode === m.id && st.modePillOn]}>
                      <Text style={[st.modeText, mode === m.id && st.modeTextOn]}>{m.label}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              )}
              <View style={st.shutterRow}>
                <View style={{ width: 64 }} />
                <TouchableOpacity style={[st.shutter, (!ready || busy) && { opacity: 0.5 }]} onPress={shoot} disabled={!ready || busy}
                  accessibilityLabel="Chụp ảnh">
                  {busy ? <ActivityIndicator color="#166534" /> : <View style={st.shutterInner} />}
                </TouchableOpacity>
                <View style={{ width: 64, alignItems: 'center' }}>
                  {!ready && !error ? <ActivityIndicator color="#fff" /> : null}
                </View>
              </View>
            </SafeAreaView>
          </>
        )}
      </View>
    </Modal>
  );
}

const st = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#000' },
  topBar: { position: 'absolute', top: 0, left: 0, right: 0, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingTop: 8 },
  topTitle: { color: '#fff', fontSize: 15, fontWeight: '700', textShadowColor: 'rgba(0,0,0,0.6)', textShadowRadius: 4 },
  iconBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: 'rgba(0,0,0,0.45)', alignItems: 'center', justifyContent: 'center' },
  iconBtnOn: { backgroundColor: 'rgba(250,204,21,0.85)' },
  iconText: { color: '#fff', fontSize: 18 },
  bottom: { position: 'absolute', left: 0, right: 0, bottom: 0, paddingHorizontal: 16, paddingBottom: 12, backgroundColor: 'rgba(0,0,0,0.35)' },
  tip: { color: '#f0fdf4', fontSize: 13, lineHeight: 18, textAlign: 'center', marginTop: 10, marginBottom: 8 },
  error: { color: '#fecaca', fontSize: 12, textAlign: 'center', marginBottom: 6 },
  modeRow: { flexDirection: 'row', justifyContent: 'center', gap: 8, marginBottom: 12 },
  modePill: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, backgroundColor: 'rgba(255,255,255,0.15)' },
  modePillOn: { backgroundColor: '#4ade80' },
  modeText: { color: '#e2e8f0', fontSize: 12, fontWeight: '600' },
  modeTextOn: { color: '#052e16', fontWeight: '800' },
  shutterRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 24 },
  shutter: { width: 76, height: 76, borderRadius: 38, borderWidth: 5, borderColor: '#fff', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.25)' },
  shutterInner: { width: 56, height: 56, borderRadius: 28, backgroundColor: '#fff' },
  permWrap: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 28, backgroundColor: '#0f172a' },
  permTitle: { color: '#fff', fontSize: 18, fontWeight: '700', textAlign: 'center', marginBottom: 8 },
  permText: { color: '#cbd5e1', fontSize: 14, textAlign: 'center', marginBottom: 20 },
  permBtn: { backgroundColor: '#16a34a', paddingHorizontal: 22, paddingVertical: 12, borderRadius: 12 },
  permBtnText: { color: '#fff', fontWeight: '700', fontSize: 15 },
});
