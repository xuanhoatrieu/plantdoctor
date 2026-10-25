// Cross-platform modals for the diagnosis screen (replaces the iOS-only Alert.prompt).
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Modal,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

export const FEEDBACK_REASONS = [
  { id: 'wrong_plant', label: 'Sai loại cây' },
  { id: 'wrong_disease', label: 'Sai bệnh' },
  { id: 'wrong_severity', label: 'Sai mức độ' },
  { id: 'wrong_treatment', label: 'Cách trị chưa hợp' },
  { id: 'other', label: 'Khác' },
];

const MAX_COMMENT = 1000;

function Sheet({ visible, onClose, children }) {
  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <KeyboardAvoidingView style={st.backdrop} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <TouchableOpacity style={StyleSheet.absoluteFill} activeOpacity={1} onPress={onClose} />
        <View style={st.sheet}>{children}</View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

/**
 * 👎 feedback form. onSubmit({reason, correctPlant, correctDisease, comment}) must return a Promise;
 * errors are shown inside the sheet so the user does not lose what they typed.
 */
export function FeedbackModal({ visible, predictionName, onClose, onSubmit }) {
  const [reason, setReason] = useState('wrong_disease');
  const [correctPlant, setCorrectPlant] = useState('');
  const [correctDisease, setCorrectDisease] = useState('');
  const [comment, setComment] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (visible) {
      setReason('wrong_disease');
      setCorrectPlant('');
      setCorrectDisease('');
      setComment('');
      setError('');
      setSending(false);
    }
  }, [visible]);

  const submit = async () => {
    setSending(true);
    setError('');
    try {
      await onSubmit({ reason, correctPlant, correctDisease, comment });
    } catch (e) {
      setError(e?.message || 'Không gửi được phản hồi. Vui lòng thử lại.');
      setSending(false);
    }
  };

  return (
    <Sheet visible={visible} onClose={sending ? () => {} : onClose}>
      <ScrollView keyboardShouldPersistTaps="handled">
        <Text style={st.title}>Góp ý kết quả chẩn đoán</Text>
        {predictionName ? <Text style={st.sub}>AI trả lời: <Text style={{ fontWeight: '700' }}>{predictionName}</Text></Text> : null}

        <Text style={st.label}>Sai ở điểm nào?</Text>
        <View style={st.chips}>
          {FEEDBACK_REASONS.map((r) => (
            <TouchableOpacity key={r.id} onPress={() => setReason(r.id)} style={[st.chip, reason === r.id && st.chipOn]}>
              <Text style={[st.chipText, reason === r.id && st.chipTextOn]}>{r.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {(reason === 'wrong_plant' || reason === 'other') && (
          <>
            <Text style={st.label}>Cây đúng là (nếu biết):</Text>
            <TextInput style={st.input} value={correctPlant} onChangeText={setCorrectPlant} maxLength={100} placeholder="vd: Bưởi Diễn" placeholderTextColor="#94a3b8" />
          </>
        )}
        {reason !== 'wrong_treatment' && (
          <>
            <Text style={st.label}>Bệnh đúng là (nếu biết):</Text>
            <TextInput style={st.input} value={correctDisease} onChangeText={setCorrectDisease} maxLength={200} placeholder="vd: Ghẻ nhám" placeholderTextColor="#94a3b8" />
          </>
        )}
        <Text style={st.label}>Ghi chú thêm:</Text>
        <TextInput style={[st.input, { height: 80, textAlignVertical: 'top' }]} value={comment} onChangeText={setComment}
          maxLength={MAX_COMMENT} multiline placeholder="Mô tả thêm triệu chứng thực tế…" placeholderTextColor="#94a3b8" />
        <Text style={st.counter}>{comment.length}/{MAX_COMMENT}</Text>

        {error ? <Text style={st.error}>{error}</Text> : null}

        <View style={st.row}>
          <TouchableOpacity style={[st.btn, st.btnGhost]} onPress={onClose} disabled={sending}>
            <Text style={st.btnGhostText}>Hủy</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[st.btn, st.btnDanger, sending && { opacity: 0.6 }]} onPress={submit} disabled={sending}>
            {sending ? <ActivityIndicator color="#fff" /> : <Text style={st.btnText}>Gửi góp ý</Text>}
          </TouchableOpacity>
        </View>
      </ScrollView>
    </Sheet>
  );
}

/** "Cây khác" in the clarification list: let the user type the crop name. */
export function CustomPlantModal({ visible, onClose, onConfirm }) {
  const [name, setName] = useState('');
  useEffect(() => { if (visible) setName(''); }, [visible]);
  const trimmed = name.trim();
  return (
    <Sheet visible={visible} onClose={onClose}>
      <Text style={st.title}>Bạn đang trồng cây gì?</Text>
      <Text style={st.sub}>Nhập tên cây để AI phân tích lại đúng loại cây.</Text>
      <TextInput style={st.input} value={name} onChangeText={setName} maxLength={100} autoFocus
        placeholder="vd: Thanh long, Mít, Hoa hồng…" placeholderTextColor="#94a3b8"
        returnKeyType="done" onSubmitEditing={() => trimmed && onConfirm(trimmed)} />
      <View style={st.row}>
        <TouchableOpacity style={[st.btn, st.btnGhost]} onPress={onClose}>
          <Text style={st.btnGhostText}>Hủy</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[st.btn, st.btnPrimary, !trimmed && { opacity: 0.5 }]} disabled={!trimmed} onPress={() => onConfirm(trimmed)}>
          <Text style={st.btnText}>Xác nhận</Text>
        </TouchableOpacity>
      </View>
    </Sheet>
  );
}

const st = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: 'rgba(15,23,42,0.55)', justifyContent: 'flex-end' },
  sheet: { backgroundColor: '#fff', borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: 20, paddingBottom: 28, maxHeight: '90%' },
  title: { fontSize: 17, fontWeight: '800', color: '#0f172a', marginBottom: 4 },
  sub: { fontSize: 12, color: '#64748b', marginBottom: 10 },
  label: { fontSize: 13, fontWeight: '600', color: '#334155', marginTop: 10, marginBottom: 6 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 16, backgroundColor: '#f1f5f9' },
  chipOn: { backgroundColor: '#dc2626' },
  chipText: { fontSize: 12, fontWeight: '600', color: '#334155' },
  chipTextOn: { color: '#fff' },
  input: { borderWidth: 1, borderColor: '#cbd5e1', borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10, fontSize: 14, color: '#0f172a' },
  counter: { fontSize: 10, color: '#94a3b8', textAlign: 'right', marginTop: 2 },
  error: { color: '#dc2626', fontSize: 12, marginTop: 8 },
  row: { flexDirection: 'row', gap: 10, marginTop: 16 },
  btn: { flex: 1, paddingVertical: 13, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  btnGhost: { borderWidth: 1, borderColor: '#cbd5e1' },
  btnGhostText: { color: '#334155', fontWeight: '600' },
  btnDanger: { backgroundColor: '#dc2626' },
  btnPrimary: { backgroundColor: '#166534' },
  btnText: { color: '#fff', fontWeight: '700', fontSize: 15 },
});
