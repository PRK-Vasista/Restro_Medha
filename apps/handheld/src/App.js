import React, { useState } from "react";
import { Button, SafeAreaView, Text, TextInput, View } from "react-native";
import { enqueue, drain, size } from "./offlineQueue";

const API = process.env.EXPO_PUBLIC_GATEWAY_URL || "http://localhost:8080";

export default function App() {
  const [orderId, setOrderId] = useState("");
  const [status, setStatus] = useState("queued");
  const [queueCount, setQueueCount] = useState(0);

  const postEvent = async (payload) => {
    await fetch(`${API}/sync/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Role": "kitchen_staff" },
      body: JSON.stringify(payload)
    });
  };

  const queueStatus = () => {
    enqueue({
      message_id: crypto.randomUUID(),
      source_device_id: "kitchen-1",
      sequence: Date.now(),
      payload: { order_id: orderId, status },
      sent_at: new Date().toISOString()
    });
    setQueueCount(size());
  };

  const syncNow = async () => {
    await drain(postEvent);
    setQueueCount(size());
  };

  return (
    <SafeAreaView style={{ padding: 24 }}>
      <Text style={{ fontSize: 24, fontWeight: "600" }}>Restro Handheld (MVP)</Text>
      <TextInput placeholder="Order ID" value={orderId} onChangeText={setOrderId} style={{ borderWidth: 1, marginTop: 12, padding: 8 }} />
      <TextInput placeholder="Status" value={status} onChangeText={setStatus} style={{ borderWidth: 1, marginTop: 12, padding: 8 }} />
      <View style={{ marginTop: 12 }}>
        <Button title="Queue Status (Offline)" onPress={queueStatus} />
      </View>
      <View style={{ marginTop: 12 }}>
        <Button title="Sync Queued Events" onPress={syncNow} />
      </View>
      <Text style={{ marginTop: 12 }}>Queued events: {queueCount}</Text>
    </SafeAreaView>
  );
}
