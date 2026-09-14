import { useState, useEffect } from 'react';
import { useForm } from '@inertiajs/react';

interface ContactoFormProps {
  contacto?: any;
  empresas: any[];
  sedes: any[];
  areas: any[];
  puestos: any[];
  contactosJefes: any[];
  cancelUrl: string;
  serverErrors?: Record<string, string>;
  errorStep?: number;
  formData?: any;
}

export default function ContactoForm({
  contacto,
  empresas = [],
  sedes = [],
  areas = [],
  puestos = [],
  contactosJefes = [],
  cancelUrl,
  serverErrors = {},
  errorStep,
  formData,
}: ContactoFormProps) {
  const [currentStep, setCurrentStep] = useState(errorStep || 1);

  const { data, setData, post, processing, errors, clearErrors } = useForm({
    primer_nombre: contacto?.primer_nombre || formData?.primer_nombre || '',
    segundo_nombre: contacto?.segundo_nombre || formData?.segundo_nombre || '',
    primer_apellido: contacto?.primer_apellido || formData?.primer_apellido || '',
    segundo_apellido: contacto?.segundo_apellido || formData?.segundo_apellido || '',
    numero_empleado: contacto?.numero_empleado || formData?.numero_empleado || '',
    fecha_nacimiento: contacto?.fecha_nacimiento || formData?.fecha_nacimiento || '',
    abreviatura_titulo: contacto?.abreviatura_titulo || formData?.abreviatura_titulo || '',
    empresa_id: contacto?.empresa?.id || formData?.empresa_id || '',
    area_id: contacto?.area_id || formData?.area_id || '',
    puesto_id: contacto?.puesto_id || formData?.puesto_id || '',
    sede_administrativa_id: contacto?.sede_administrativa_id || formData?.sede_administrativa_id || '',
    jefe_directo_id: contacto?.jefe_directo_id || formData?.jefe_directo_id || '',
    fecha_ingreso: contacto?.fecha_ingreso || formData?.fecha_ingreso || '',
    fecha_egreso: contacto?.fecha_egreso || formData?.fecha_egreso || '',
    mostrar_en_directorio: contacto?.mostrar_en_directorio ?? true,
    mostrar_en_cumpleanios: contacto?.mostrar_en_cumpleanios ?? true,
    es_jefe: contacto?.es_jefe ?? false,
    esta_archivado: contacto?.esta_archivado ?? false,
    crear_usuario_sistema: false,
    emails: contacto?.emails?.length ? contacto.emails : [{ email: '', es_principal: true, es_slack: false }],
    telefonos: contacto?.telefonos?.length ? contacto.telefonos : [{ telefono: '', extension: '', es_principal: true, es_celular: false }],
  });

  // Combinación de errores locales de useForm y los recibidos del backend
  const activeErrors = { ...errors, ...serverErrors };

  useEffect(() => {
    if (errorStep) setCurrentStep(errorStep);
  }, [errorStep, serverErrors]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const url = contacto?.id ? `/directorio/contacto/editar/${contacto.id}/` : '/directorio/contacto/crear/';
    post(url);
  };

  // Sub-recursos helpers
  const handleEmailChange = (index: number, field: string, value: any) => {
    const updated = [...data.emails];
    if (field === 'es_principal' && value) {
      updated.forEach((e, i) => (e.es_principal = i === index));
    } else {
      updated[index][field] = value;
    }
    setData('emails', updated);
  };

  const addEmail = () => setData('emails', [...data.emails, { email: '', es_principal: data.emails.length === 0, es_slack: false }]);
  const removeEmail = (index: number) => setData('emails', data.emails.filter((_, i) => i !== index));

  const handleTelefonoChange = (index: number, field: string, value: any) => {
    const updated = [...data.telefonos];
    if (field === 'es_principal' && value) {
      updated.forEach((t, i) => (t.es_principal = i === index));
    } else {
      updated[index][field] = value;
    }
    setData('telefonos', updated);
  };

  const addTelefono = () => setData('telefonos', [...data.telefonos, { telefono: '', extension: '', es_principal: data.telefonos.length === 0, es_celular: false }]);
  const removeTelefono = (index: number) => setData('telefonos', data.telefonos.filter((_, i) => i !== index));

  const steps = [
    { id: 1, title: 'Identidad', desc: 'Datos personales e identificación' },
    { id: 2, title: 'Organización', desc: 'Ubicación, empresa y rol' },
    { id: 3, title: 'Contacto', desc: 'Canales de comunicación' },
    { id: 4, title: 'Ajustes y Acceso', desc: 'Permisos, fechas y cuenta' },
  ];

  return (
    <div className="space-y-6">
      {/* Wizard Step Indicator */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        {steps.map((step) => {
          const isActive = currentStep === step.id;
          const isDone = currentStep > step.id;
          return (
            <button
              key={step.id}
              type="button"
              onClick={() => setCurrentStep(step.id)}
              className={`p-3.5 rounded-xl border text-left transition-all ${
                isActive
                  ? 'border-indigo-600 bg-indigo-50/50 shadow-sm ring-1 ring-indigo-600'
                  : isDone
                  ? 'border-emerald-200 bg-emerald-50/40'
                  : 'border-slate-200 bg-white hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <span className={`w-6 h-6 rounded-full text-xs font-bold flex items-center justify-center shrink-0 ${
                  isActive ? 'bg-indigo-600 text-white' : isDone ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-600'
                }`}>
                  {isDone ? '✓' : step.id}
                </span>
                <span className="font-semibold text-sm text-slate-800">{step.title}</span>
              </div>
              <p className="text-xs text-slate-500 mt-1 pl-8">{step.desc}</p>
            </button>
          );
        })}
      </div>

      <form onSubmit={handleSubmit} className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">

        {/* PASO 1: IDENTIDAD */}
        {currentStep === 1 && (
          <div className="space-y-4">
            <h3 className="text-base font-bold text-slate-800 border-b pb-2">Datos Personales</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Primer Nombre *</label>
                <input
                  type="text"
                  value={data.primer_nombre}
                  onChange={(e) => setData('primer_nombre', e.target.value)}
                  className={`w-full border rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none ${activeErrors.primer_nombre ? 'border-red-500 bg-red-50/20' : 'border-slate-300'}`}
                />
                {activeErrors.primer_nombre && <span className="text-xs text-red-500 mt-1 block">{activeErrors.primer_nombre}</span>}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Segundo Nombre</label>
                <input
                  type="text"
                  value={data.segundo_nombre}
                  onChange={(e) => setData('segundo_nombre', e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Primer Apellido *</label>
                <input
                  type="text"
                  value={data.primer_apellido}
                  onChange={(e) => setData('primer_apellido', e.target.value)}
                  className={`w-full border rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none ${activeErrors.primer_apellido ? 'border-red-500 bg-red-50/20' : 'border-slate-300'}`}
                />
                {activeErrors.primer_apellido && <span className="text-xs text-red-500 mt-1 block">{activeErrors.primer_apellido}</span>}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Segundo Apellido</label>
                <input
                  type="text"
                  value={data.segundo_apellido}
                  onChange={(e) => setData('segundo_apellido', e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Nº Empleado</label>
                <input
                  type="text"
                  value={data.numero_empleado}
                  onChange={(e) => setData('numero_empleado', e.target.value)}
                  className={`w-full border rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none ${activeErrors.numero_empleado ? 'border-red-500 bg-red-50/20' : 'border-slate-300'}`}
                />
                {activeErrors.numero_empleado && <span className="text-xs text-red-500 mt-1 block">{activeErrors.numero_empleado}</span>}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Título Abreviado (ej. Ing., Lic.)</label>
                <input
                  type="text"
                  value={data.abreviatura_titulo}
                  onChange={(e) => setData('abreviatura_titulo', e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Fecha de Nacimiento</label>
                <input
                  type="date"
                  value={data.fecha_nacimiento}
                  onChange={(e) => setData('fecha_nacimiento', e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>
            </div>
          </div>
        )}

        {/* PASO 2: ORGANIZACIÓN */}
        {currentStep === 2 && (
          <div className="space-y-4">
            <h3 className="text-base font-bold text-slate-800 border-b pb-2">Estructura Organizacional</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Empresa</label>
                <select
                  value={data.empresa_id}
                  onChange={(e) => setData('empresa_id', e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                >
                  <option value="">Selecciona una Empresa</option>
                  {empresas.map((emp) => (
                    <option key={emp.id} value={emp.id}>{emp.nombre}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Área / Departamento</label>
                <select
                  value={data.area_id}
                  onChange={(e) => setData('area_id', e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                >
                  <option value="">Selecciona un Área</option>
                  {areas.map((area) => (
                    <option key={area.id} value={area.id}>{area.nombre}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Puesto</label>
                <select
                  value={data.puesto_id}
                  onChange={(e) => setData('puesto_id', e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                >
                  <option value="">Selecciona un Puesto</option>
                  {puestos.map((puesto) => (
                    <option key={puesto.id} value={puesto.id}>{puesto.nombre}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Sede Administrativa</label>
                <select
                  value={data.sede_administrativa_id}
                  onChange={(e) => setData('sede_administrativa_id', e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                >
                  <option value="">Selecciona una Sede</option>
                  {sedes.map((sede) => (
                    <option key={sede.id} value={sede.id}>{sede.nombre}</option>
                  ))}
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-slate-700 mb-1">Jefe Directo</label>
                <select
                  value={data.jefe_directo_id}
                  onChange={(e) => setData('jefe_directo_id', e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                >
                  <option value="">Sin Jefe Directo Asignado</option>
                  {contactosJefes.map((jefe) => (
                    <option key={jefe.id} value={jefe.id}>{jefe.nombre_completo}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}

        {/* PASO 3: CONTACTO */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <h3 className="text-base font-bold text-slate-800 border-b pb-2">Canales de Comunicación</h3>

            {/* Correos */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">Correos Electrónicos</h4>
                <button type="button" onClick={addEmail} className="text-xs text-indigo-600 font-semibold hover:underline">
                  + Agregar Correo
                </button>
              </div>
              {activeErrors.emails && <p className="text-xs text-red-500">{activeErrors.emails}</p>}

              {data.emails.map((em: any, idx: number) => (
                <div key={idx} className="flex flex-col gap-1 border border-slate-200 p-3 rounded-lg bg-slate-50/50">
                  <div className="flex items-center gap-3">
                    <input
                      type="email"
                      placeholder="ejemplo@empresa.com"
                      value={em.email}
                      onChange={(e) => handleEmailChange(idx, 'email', e.target.value)}
                      className="flex-1 border border-slate-300 rounded-lg p-2 text-sm bg-white"
                    />
                    <label className="flex items-center gap-1.5 text-xs text-slate-600 cursor-pointer">
                      <input
                        type="radio"
                        name="email_principal"
                        checked={em.es_principal}
                        onChange={(e) => handleEmailChange(idx, 'es_principal', e.target.checked)}
                      />
                      Principal
                    </label>
                    <label className="flex items-center gap-1.5 text-xs text-slate-600 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={em.es_slack}
                        onChange={(e) => handleEmailChange(idx, 'es_slack', e.target.checked)}
                      />
                      Slack
                    </label>
                    {data.emails.length > 1 && (
                      <button type="button" onClick={() => removeEmail(idx)} className="text-red-500 hover:text-red-700 text-xs px-2">
                        Eliminar
                      </button>
                    )}
                  </div>
                  {activeErrors[`emails.${idx}.email`] && (
                    <span className="text-xs text-red-500 mt-1">{activeErrors[`emails.${idx}.email`]}</span>
                  )}
                </div>
              ))}
            </div>

            {/* Teléfonos */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">Teléfonos</h4>
                <button type="button" onClick={addTelefono} className="text-xs text-indigo-600 font-semibold hover:underline">
                  + Agregar Teléfono
                </button>
              </div>

              {data.telefonos.map((tel: any, idx: number) => (
                <div key={idx} className="flex flex-col gap-1 border border-slate-200 p-3 rounded-lg bg-slate-50/50">
                  <div className="flex items-center gap-3">
                    <input
                      type="text"
                      placeholder="Número telefónico"
                      value={tel.telefono}
                      onChange={(e) => handleTelefonoChange(idx, 'telefono', e.target.value)}
                      className="flex-1 border border-slate-300 rounded-lg p-2 text-sm bg-white"
                    />
                    <input
                      type="text"
                      placeholder="Ext."
                      value={tel.extension || ''}
                      onChange={(e) => handleTelefonoChange(idx, 'extension', e.target.value)}
                      className="w-20 border border-slate-300 rounded-lg p-2 text-sm bg-white"
                    />
                    <label className="flex items-center gap-1.5 text-xs text-slate-600 cursor-pointer">
                      <input
                        type="radio"
                        name="telefono_principal"
                        checked={tel.es_principal}
                        onChange={(e) => handleTelefonoChange(idx, 'es_principal', e.target.checked)}
                      />
                      Principal
                    </label>
                    <label className="flex items-center gap-1.5 text-xs text-slate-600 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={tel.es_celular}
                        onChange={(e) => handleTelefonoChange(idx, 'es_celular', e.target.checked)}
                      />
                      Celular
                    </label>
                    {data.telefonos.length > 1 && (
                      <button type="button" onClick={() => removeTelefono(idx)} className="text-red-500 hover:text-red-700 text-xs px-2">
                        Eliminar
                      </button>
                    )}
                  </div>
                  {activeErrors[`telefonos.${idx}.telefono`] && (
                    <span className="text-xs text-red-500 mt-1">{activeErrors[`telefonos.${idx}.telefono`]}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* PASO 4: AJUSTES Y CUENTA */}
        {currentStep === 4 && (
          <div className="space-y-6">
            <h3 className="text-base font-bold text-slate-800 border-b pb-2">Configuración y Visibilidad</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Fecha de Ingreso</label>
                <input
                  type="date"
                  value={data.fecha_ingreso}
                  onChange={(e) => setData('fecha_ingreso', e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Fecha de Egreso</label>
                <input
                  type="date"
                  value={data.fecha_egreso}
                  onChange={(e) => setData('fecha_egreso', e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              <label className="flex items-center gap-3 p-3 border rounded-xl hover:bg-slate-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={data.mostrar_en_directorio}
                  onChange={(e) => setData('mostrar_en_directorio', e.target.checked)}
                  className="w-4 h-4 text-indigo-600 rounded"
                />
                <span className="text-xs font-medium text-slate-700">Mostrar en el directorio público</span>
              </label>

              <label className="flex items-center gap-3 p-3 border rounded-xl hover:bg-slate-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={data.mostrar_en_cumpleanios}
                  onChange={(e) => setData('mostrar_en_cumpleanios', e.target.checked)}
                  className="w-4 h-4 text-indigo-600 rounded"
                />
                <span className="text-xs font-medium text-slate-700">Mostrar en la lista de cumpleaños</span>
              </label>

              <label className="flex items-center gap-3 p-3 border rounded-xl hover:bg-slate-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={data.es_jefe}
                  onChange={(e) => setData('es_jefe', e.target.checked)}
                  className="w-4 h-4 text-indigo-600 rounded"
                />
                <span className="text-xs font-medium text-slate-700">Marcar como Jefe Directo</span>
              </label>

              <label className="flex items-center gap-3 p-3 border rounded-xl hover:bg-slate-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={data.esta_archivado}
                  onChange={(e) => setData('esta_archivado', e.target.checked)}
                  className="w-4 h-4 text-indigo-600 rounded"
                />
                <span className="text-xs font-medium text-slate-700">Archivar Contacto</span>
              </label>
            </div>

            <div className="bg-indigo-50/70 p-4 rounded-xl border border-indigo-100 flex items-center justify-between mt-4">
              <div>
                <h4 className="text-sm font-bold text-indigo-900">¿Crear usuario de acceso al sistema?</h4>
                <p className="text-xs text-indigo-700">Genera credenciales de inicio de sesión asociadas a este contacto.</p>
              </div>
              <input
                type="checkbox"
                checked={data.crear_usuario_sistema}
                onChange={(e) => setData('crear_usuario_sistema', e.target.checked)}
                className="w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500"
              />
            </div>
          </div>
        )}

        {/* Acciones del Wizard */}
        <div className="pt-4 border-t border-slate-200 flex items-center justify-between">
          <button
            type="button"
            disabled={currentStep === 1}
            onClick={() => setCurrentStep((prev) => Math.max(1, prev - 1))}
            className="px-4 py-2 border border-slate-300 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-40"
          >
            Anterior
          </button>

          <div className="flex items-center gap-3">
            {currentStep < 4 ? (
              <button
                type="button"
                onClick={() => setCurrentStep((prev) => Math.min(4, prev + 1))}
                className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm"
              >
                Siguiente
              </button>
            ) : (
              <button
                type="submit"
                disabled={processing}
                className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-sm disabled:opacity-50"
              >
                {processing ? 'Guardando...' : contacto?.id ? 'Guardar Cambios' : 'Crear Contacto'}
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}