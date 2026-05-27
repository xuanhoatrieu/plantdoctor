import { Tabs } from 'expo-router';
import { Platform, View, Text } from 'react-native';

function TabIcon({ emoji, label, focused }) {
  return (
    <View style={{ alignItems: 'center', justifyContent: 'center', width: 60 }}>
      <Text style={{ fontSize: 22 }}>{emoji}</Text>
      <Text style={{ fontSize: 10, marginTop: 2, color: focused ? '#16a34a' : '#9ca3af', fontWeight: focused ? '700' : '500' }}>{label}</Text>
    </View>
  );
}

export default function Layout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarShowLabel: false,
        tabBarStyle: {
          height: Platform.OS === 'ios' ? 88 : 68,
          paddingBottom: Platform.OS === 'ios' ? 24 : 8,
          paddingTop: 8,
          borderTopWidth: 1,
          borderTopColor: '#e5e7eb',
        },
      }}
    >
      <Tabs.Screen name="index" options={{ tabBarIcon: ({ focused }) => <TabIcon emoji="🔍" label="Chẩn đoán" focused={focused} /> }} />
      <Tabs.Screen name="history" options={{ tabBarIcon: ({ focused }) => <TabIcon emoji="📜" label="Lịch sử" focused={focused} /> }} />
      <Tabs.Screen name="library" options={{ tabBarIcon: ({ focused }) => <TabIcon emoji="📚" label="Thư viện" focused={focused} /> }} />
      <Tabs.Screen name="pesticides" options={{ tabBarIcon: ({ focused }) => <TabIcon emoji="🧪" label="Thuốc" focused={focused} /> }} />
      <Tabs.Screen name="profile" options={{ tabBarIcon: ({ focused }) => <TabIcon emoji="👤" label="Tôi" focused={focused} /> }} />
      <Tabs.Screen name="admin" options={{ href: null }} />
    </Tabs>
  );
}
