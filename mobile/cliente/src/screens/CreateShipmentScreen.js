import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Modal,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme-context';
import Input from '../shared/components/Input';
import Button from '../shared/components/Button';
import Card from '../shared/components/Card';
import { post } from '../shared/api';
import { formatCurrency } from '../shared/formatters';
import { validateRequired, validatePhone } from '../shared/validators';
import { colors, typography, spacing, borderRadius, shadows } from '../shared/theme';

const SERVICE_TYPES = [
  {
    id: 'express',
    name: 'Express',
    time: '2-4 hrs',
    icon: 'flash',
    color: colors.error[500],
    multiplier: 1.5,
  },
  {
    id: 'estandar',
    name: 'Estándar',
    time: '24-48 hrs',
    icon: 'time',
    color: colors.primary[500],
    multiplier: 1.0,
  },
  {
    id: 'economico',
    name: 'Económico',
    time: '48-72 hrs',
    icon: 'leaf',
    color: colors.success[500],
    multiplier: 0.7,
  },
];

export default function CreateShipmentScreen({ navigation }) {
  const { theme } = useTheme();
  const [loading, setLoading] = useState(false);
  const [showSummary, setShowSummary] = useState(false);

  // Origin
  const [originAddress, setOriginAddress] = useState('');
  const [originContact, setOriginContact] = useState('');
  const [originPhone, setOriginPhone] = useState('');
  const [originAddressError, setOriginAddressError] = useState('');
  const [originContactError, setOriginContactError] = useState('');
  const [originPhoneError, setOriginPhoneError] = useState('');

  // Destination
  const [destAddress, setDestAddress] = useState('');
  const [destContact, setDestContact] = useState('');
  const [destPhone, setDestPhone] = useState('');
  const [destAddressError, setDestAddressError] = useState('');
  const [destContactError, setDestContactError] = useState('');
  const [destPhoneError, setDestPhoneError] = useState('');

  // Package
  const [weight, setWeight] = useState('');
  const [dimensions, setDimensions] = useState('');
  const [description, setDescription] = useState('');
  const [declaredValue, setDeclaredValue] = useState('');
  const [weightError, setWeightError] = useState('');
  const [descriptionError, setDescriptionError] = useState('');

  // Service
  const [serviceType, setServiceType] = useState('estandar');
  const [pickupTime, setPickupTime] = useState('');

  const baseCost = 85;
  const selectedService = SERVICE_TYPES.find((s) => s.id === serviceType);
  const weightCost = weight ? parseFloat(weight) * 12 : 0;
  const estimatedCost = (baseCost + weightCost) * (selectedService?.multiplier || 1);

  const validateForm = () => {
    let valid = true;

    const addr1 = validateRequired(originAddress, 'Dirección de recogida');
    if (!addr1.valid) { setOriginAddressError(addr1.error); valid = false; } else { setOriginAddressError(''); }

    const cnt1 = validateRequired(originContact, 'Contacto de recogida');
    if (!cnt1.valid) { setOriginContactError(cnt1.error); valid = false; } else { setOriginContactError(''); }

    const ph1 = validatePhone(originPhone);
    if (!ph1.valid) { setOriginPhoneError(ph1.error); valid = false; } else { setOriginPhoneError(''); }

    const addr2 = validateRequired(destAddress, 'Dirección de entrega');
    if (!addr2.valid) { setDestAddressError(addr2.error); valid = false; } else { setDestAddressError(''); }

    const cnt2 = validateRequired(destContact, 'Contacto de entrega');
    if (!cnt2.valid) { setDestContactError(cnt2.error); valid = false; } else { setDestContactError(''); }

    const ph2 = validatePhone(destPhone);
    if (!ph2.valid) { setDestPhoneError(ph2.error); valid = false; } else { setDestPhoneError(''); }

    const wgt = validateRequired(weight, 'Peso');
    if (!wgt.valid) { setWeightError(wgt.error); valid = false; } else { setWeightError(''); }

    const desc = validateRequired(description, 'Descripción');
    if (!desc.valid) { setDescriptionError(desc.error); valid = false; } else { setDescriptionError(''); }

    return valid;
  };

  const handleCreate = () => {
    if (!validateForm()) return;
    setShowSummary(true);
  };

  const confirmCreate = async () => {
    setShowSummary(false);
    setLoading(true);
    try {
      const payload = {
        origin_address: originAddress,
        origin_contact: originContact,
        origin_phone: originPhone,
        destination_address: destAddress,
        destination_contact: destContact,
        destination_phone: destPhone,
        weight_kg: parseFloat(weight) || 0,
        dimensions: dimensions || null,
        description,
        declared_value: parseFloat(declaredValue) || 0,
        service_type: serviceType,
        pickup_time: pickupTime || null,
      };
      await post('/api/shipments', payload);
      Alert.alert('Envío creado', 'Tu envío ha sido registrado exitosamente.', [
        { text: 'Ver envío', onPress: () => navigation.goBack() },
      ]);
    } catch (error) {
      Alert.alert('Error', error?.message || 'No se pudo crear el envío. Intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: theme.background }]}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color={theme.text} />
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: theme.text }]}>Nuevo envío</Text>
          <View style={{ width: 40 }} />
        </View>

        {/* Origin Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Ionicons name="location" size={20} color={colors.primary[500]} />
            <Text style={[styles.sectionTitle, { color: theme.text }]}>Origen - Recogida</Text>
          </View>
          <Input
            label="Dirección de recogida"
            value={originAddress}
            onChangeText={(t) => { setOriginAddress(t); if (originAddressError) setOriginAddressError(''); }}
            placeholder="Calle, número, colonia, ciudad"
            error={originAddressError}
            icon={<Ionicons name="location-outline" size={20} color={colors.neutral[400]} />}
            rightIcon={
              <TouchableOpacity onPress={() => Alert.alert('Ubicación', 'Usando ubicación actual')}>
                <Ionicons name="navigate" size={20} color={colors.primary[500]} />
              </TouchableOpacity>
            }
            required
          />
          <Input
            label="Nombre del contacto"
            value={originContact}
            onChangeText={(t) => { setOriginContact(t); if (originContactError) setOriginContactError(''); }}
            placeholder="Nombre completo"
            error={originContactError}
            icon={<Ionicons name="person-outline" size={20} color={colors.neutral[400]} />}
            required
          />
          <Input
            label="Teléfono del contacto"
            value={originPhone}
            onChangeText={(t) => { setOriginPhone(t); if (originPhoneError) setOriginPhoneError(''); }}
            placeholder="10 dígitos"
            error={originPhoneError}
            keyboardType="phone-pad"
            icon={<Ionicons name="call-outline" size={20} color={colors.neutral[400]} />}
            required
          />
        </View>

        {/* Destination Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Ionicons name="flag" size={20} color={colors.success[500]} />
            <Text style={[styles.sectionTitle, { color: theme.text }]}>Destino - Entrega</Text>
          </View>
          <Input
            label="Dirección de entrega"
            value={destAddress}
            onChangeText={(t) => { setDestAddress(t); if (destAddressError) setDestAddressError(''); }}
            placeholder="Calle, número, colonia, ciudad"
            error={destAddressError}
            icon={<Ionicons name="location-outline" size={20} color={colors.neutral[400]} />}
            required
          />
          <Input
            label="Nombre del contacto"
            value={destContact}
            onChangeText={(t) => { setDestContact(t); if (destContactError) setDestContactError(''); }}
            placeholder="Nombre completo"
            error={destContactError}
            icon={<Ionicons name="person-outline" size={20} color={colors.neutral[400]} />}
            required
          />
          <Input
            label="Teléfono del contacto"
            value={destPhone}
            onChangeText={(t) => { setDestPhone(t); if (destPhoneError) setDestPhoneError(''); }}
            placeholder="10 dígitos"
            error={destPhoneError}
            keyboardType="phone-pad"
            icon={<Ionicons name="call-outline" size={20} color={colors.neutral[400]} />}
            required
          />
        </View>

        {/* Package Details */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Ionicons name="cube" size={20} color={colors.accent[500]} />
            <Text style={[styles.sectionTitle, { color: theme.text }]}>Detalles del paquete</Text>
          </View>
          <Input
            label="Peso (kg)"
            value={weight}
            onChangeText={(t) => { setWeight(t); if (weightError) setWeightError(''); }}
            placeholder="0.0"
            error={weightError}
            keyboardType="decimal-pad"
            icon={<Ionicons name="scale-outline" size={20} color={colors.neutral[400]} />}
            required
          />
          <Input
            label="Dimensiones (opcional)"
            value={dimensions}
            onChangeText={setDimensions}
            placeholder="L x A x Alto (cm)"
            icon={<Ionicons name="resize-outline" size={20} color={colors.neutral[400]} />}
          />
          <Input
            label="Descripción del contenido"
            value={description}
            onChangeText={(t) => { setDescription(t); if (descriptionError) setDescriptionError(''); }}
            placeholder="Describe el contenido del paquete"
            error={descriptionError}
            icon={<Ionicons name="document-text-outline" size={20} color={colors.neutral[400]} />}
            required
          />
          <Input
            label="Valor declarado (opcional)"
            value={declaredValue}
            onChangeText={setDeclaredValue}
            placeholder="$0.00"
            keyboardType="decimal-pad"
            icon={<Ionicons name="cash-outline" size={20} color={colors.neutral[400]} />}
          />
        </View>

        {/* Service Type */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Ionicons name="rocket" size={20} color="#7c3aed" />
            <Text style={[styles.sectionTitle, { color: theme.text }]}>Tipo de servicio</Text>
          </View>
          <View style={styles.serviceOptions}>
            {SERVICE_TYPES.map((service) => (
              <TouchableOpacity
                key={service.id}
                style={[
                  styles.serviceOption,
                  {
                    backgroundColor: serviceType === service.id ? service.color + '15' : theme.surface,
                    borderColor: serviceType === service.id ? service.color : theme.border,
                  },
                ]}
                onPress={() => setServiceType(service.id)}
                activeOpacity={0.7}
              >
                <Ionicons
                  name={service.icon}
                  size={24}
                  color={serviceType === service.id ? service.color : theme.textSecondary}
                />
                <Text
                  style={[
                    styles.serviceName,
                    {
                      color: serviceType === service.id ? service.color : theme.text,
                      fontWeight: serviceType === service.id ? '700' : '500',
                    },
                  ]}
                >
                  {service.name}
                </Text>
                <Text style={[styles.serviceTime, { color: theme.textSecondary }]}>
                  {service.time}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Cost Estimate */}
        <Card style={[styles.costCard, { backgroundColor: theme.surface }]}>
          <Text style={[styles.costTitle, { color: theme.textSecondary }]}>Costo estimado</Text>
          <Text style={[styles.costAmount, { color: theme.primary }]}>{formatCurrency(estimatedCost)}</Text>
          <Text style={[styles.costNote, { color: theme.textDisabled }]}>
            El costo final puede variar según la distancia real
          </Text>
        </Card>

        {/* Create Button */}
        <Button
          title="Crear envío"
          onPress={handleCreate}
          loading={loading}
          disabled={loading}
          size="lg"
          style={styles.createButton}
        />

        <View style={{ height: 40 }} />
      </ScrollView>

      {/* Summary Modal */}
      <Modal visible={showSummary} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: theme.surface }]}>
            <Text style={[styles.modalTitle, { color: theme.text }]}>Resumen del envío</Text>

            <View style={styles.summarySection}>
              <Text style={[styles.summaryLabel, { color: theme.textSecondary }]}>Origen</Text>
              <Text style={[styles.summaryValue, { color: theme.text }]}>{originAddress}</Text>
              <Text style={[styles.summaryContact, { color: theme.textSecondary }]}>
                {originContact} · {originPhone}
              </Text>
            </View>

            <View style={styles.summaryDivider} />

            <View style={styles.summarySection}>
              <Text style={[styles.summaryLabel, { color: theme.textSecondary }]}>Destino</Text>
              <Text style={[styles.summaryValue, { color: theme.text }]}>{destAddress}</Text>
              <Text style={[styles.summaryContact, { color: theme.textSecondary }]}>
                {destContact} · {destPhone}
              </Text>
            </View>

            <View style={styles.summaryDivider} />

            <View style={styles.summaryRow}>
              <Text style={[styles.summaryLabel, { color: theme.textSecondary }]}>Servicio</Text>
              <Text style={[styles.summaryValue, { color: theme.text }]}>{selectedService?.name}</Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={[styles.summaryLabel, { color: theme.textSecondary }]}>Peso</Text>
              <Text style={[styles.summaryValue, { color: theme.text }]}>{weight} kg</Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={[styles.summaryLabel, { color: theme.textSecondary }]}>Costo</Text>
              <Text style={[styles.summaryCost, { color: theme.primary }]}>{formatCurrency(estimatedCost)}</Text>
            </View>

            <View style={styles.modalActions}>
              <Button
                title="Cancelar"
                onPress={() => setShowSummary(false)}
                variant="secondary"
                style={styles.modalButton}
              />
              <Button
                title="Confirmar"
                onPress={confirmCreate}
                loading={loading}
                style={styles.modalButton}
              />
            </View>
          </View>
        </View>
      </Modal>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: spacing[4],
    paddingTop: spacing[10],
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing[6],
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: typography.fontSize.xl,
    fontWeight: '700',
  },
  section: {
    marginBottom: spacing[6],
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing[2],
    marginBottom: spacing[3],
  },
  sectionTitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: '700',
  },
  serviceOptions: {
    flexDirection: 'row',
    gap: spacing[3],
  },
  serviceOption: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: spacing[4],
    paddingHorizontal: spacing[2],
    borderRadius: borderRadius.lg,
    borderWidth: 2,
  },
  serviceName: {
    fontSize: typography.fontSize.sm,
    marginTop: spacing[2],
    marginBottom: 2,
  },
  serviceTime: {
    fontSize: typography.fontSize.xs,
  },
  costCard: {
    alignItems: 'center',
    marginBottom: spacing[6],
    paddingVertical: spacing[6],
  },
  costTitle: {
    fontSize: typography.fontSize.sm,
    fontWeight: '500',
    marginBottom: spacing[1],
  },
  costAmount: {
    fontSize: typography.fontSize['3xl'],
    fontWeight: '800',
    marginBottom: spacing[1],
  },
  costNote: {
    fontSize: typography.fontSize.xs,
  },
  createButton: {
    width: '100%',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    borderTopLeftRadius: borderRadius.xl,
    borderTopRightRadius: borderRadius.xl,
    padding: spacing[6],
    maxHeight: '80%',
  },
  modalTitle: {
    fontSize: typography.fontSize.xl,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: spacing[5],
  },
  summarySection: {
    marginBottom: spacing[3],
  },
  summaryLabel: {
    fontSize: typography.fontSize.xs,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  summaryValue: {
    fontSize: typography.fontSize.base,
    fontWeight: '600',
  },
  summaryContact: {
    fontSize: typography.fontSize.sm,
    marginTop: 2,
  },
  summaryDivider: {
    height: 1,
    backgroundColor: colors.neutral[200],
    marginVertical: spacing[3],
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing[2],
  },
  summaryCost: {
    fontSize: typography.fontSize.xl,
    fontWeight: '800',
  },
  modalActions: {
    flexDirection: 'row',
    gap: spacing[3],
    marginTop: spacing[5],
  },
  modalButton: {
    flex: 1,
  },
});
