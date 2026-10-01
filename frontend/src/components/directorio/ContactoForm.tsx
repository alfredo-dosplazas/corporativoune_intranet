import React, { useState } from 'react';
import { useForm, Link } from '@inertiajs/react';

interface ContactoFormProps {
  contacto?: any;
  empresas: any[];
  sedes: any[];
  areas: any[];
  puestos: any[];
  contactosJefes: any[];
  cancelUrl: string;
  serverErrors?: Record<string, any>;
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
  formData,
}: ContactoFormProps) {
  const [photoPreview, setPhotoPreview] = useState<string | null>(contacto?.foto || null);

  const { data, setData, post, processing, errors } = useForm({
    foto: null as File | null,
    primer_nombre: contacto?.primer_nombre || formData?.primer_nombre || '',
    segundo_nombre: contacto?.segundo_nombre || formData?.segundo_nombre || '',
    primer_apellido: contacto?.primer_apellido || formData?.primer_apellido || '',
    segundo_apellido: contacto?.segundo_apellido || formData?.segundo_apellido || '',
    numero_empleado: contacto?.numero_empleado || formData?.numero_empleado || '',
    fecha_nacimiento: contacto?.fecha_nacimiento || formData?.fecha_nacimiento || '',
    abreviatura_titulo: contacto?.abreviatura_titulo || formData?.abreviatura_titulo || '',
    empresa_id: contacto?.empresa?.id || formData?.empresa_id || '',
    area_id: contacto?.area?.id || formData?.area_id || '',
    puesto_id: contacto?.puesto?.id || formData?.puesto_id || '',
    sede_administrativa_id: contacto?.sede_administrativa?.id || formData?.sede_administrativa_id || '',
    jefe_directo_id: contacto?.jefe_directo?.id || formData?.jefe_directo_id || '',
    fecha_ingreso: contacto?.fecha_ingreso || formData?.fecha_ingreso || '',
    fecha_egreso: contacto?.fecha_egreso || formData?.fecha_egreso || '',
    mostrar_en_directorio: contacto?.mostrar_en_directorio ?? true,
    mostrar_en_cumpleanios: contacto?.mostrar_en_cumpleanios ?? true,
    es_jefe: contacto?.es_jefe ?? false,
    esta_archivado: contacto?.esta_archivado ?? false,
    emails: contacto?.emails?.length ? contacto.emails : [{ email: '', es_principal: true, es_slack: false }],
    telefonos: contacto?.telefonos?.length ? contacto.telefonos : [{ telefono: '', extension: '', es_principal: true, es_celular: false }],
  });

  const mergedErrors = { ...errors, ...serverErrors };

  const getErrorMessage = (key: string) => {
    const err = mergedErrors[key];
    if (!err) return null;
    if (typeof err === 'string') return err;
    if (Array.isArray(err) && err[0]?.message) return err[0].message;
    return null;
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setData('foto', file);
      setPhotoPreview(URL.createObjectURL(file));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const url = contacto?.id ? `/directorio/contacto/editar/${contacto.id}/` : '/directorio/contacto/crear/';

    // Si incluye archivo, Inertia envía automáticamente como FormData
    post(url, {
      forceFormData: true,
    });
  };

  // Handlers para Múltiples Correos
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

  // Handlers para Múltiples Teléfonos
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

  const hasErrorsInSection = (fields: string[]) => {
    return fields.some((field) => Boolean(getErrorMessage(field)) || Object.keys(mergedErrors).some(k => k.startsWith(field)));
  };

  const errorCount = Object.keys(mergedErrors).length;

  return (
    <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">

      {/* NAVEGACIÓN RÁPIDA / SUMMARY SIDEBAR */}
      <div className="lg:col-span-1 lg:sticky lg:top-6 space-y-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Secciones del Formulario</h3>
          <nav className="space-y-1">
            <a
              href="#sec-foto"
              className={`flex items-center justify-between p-2 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 ${
                hasErrorsInSection(['foto']) ? 'text-red-600 font-semibold' : ''
              }`}
            >
              <span>1. Fotografía</span>
            </a>
            <a
              href="#sec-identidad"
              className={`flex items-center justify-between p-2 rounded-lg text-xs font-medium ${
                hasErrorsInSection(['primer_nombre', 'primer_apellido', 'numero_empleado']) ? 'text-red-600 bg-red-50 font-semibold' : 'text-slate-700 hover:bg-slate-50'
              }`}
            >
              <span>2. Datos Personales</span>
              {hasErrorsInSection(['primer_nombre', 'primer_apellido', 'numero_empleado']) && (
                <span className="w-2 h-2 bg-red-500 rounded-full"></span>
              )}
            </a>
            <a
              href="#sec-organizacion"
              className={`flex items-center justify-between p-2 rounded-lg text-xs font-medium ${
                hasErrorsInSection(['empresa_id', 'area_id', 'puesto_id', 'sede_administrativa_id']) ? 'text-red-600 bg-red-50 font-semibold' : 'text-slate-700 hover:bg-slate-50'
              }`}
            >
              <span>3. Estructura Laboral</span>
            </a>
            <a
              href="#sec-contacto"
              className={`flex items-center justify-between p-2 rounded-lg text-xs font-medium ${
                hasErrorsInSection(['emails', 'telefonos']) ? 'text-red-600 bg-red-50 font-semibold' : 'text-slate-700 hover:bg-slate-50'
              }`}
            >
              <span>4. Contacto Directo</span>
              {hasErrorsInSection(['emails', 'telefonos']) && (
                <span className="w-2 h-2 bg-red-500 rounded-full"></span>
              )}
            </a>
            <a
              href="#sec-configuracion"
              className="flex items-center justify-between p-2 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50"
            >
              <span>5. Configuración y Visibilidad</span>
            </a>
          </nav>

          <div className="pt-3 border-t border-slate-100 space-y-2">
            {errorCount > 0 && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
                <p className="font-bold">Hay {errorCount} error(es) en el formulario.</p>
                <p className="text-[11px] mt-0.5">Por favor corrige los campos indicados en rojo.</p>
              </div>
            )}

            <button
              type="submit"
              disabled={processing}
              className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium text-sm rounded-lg shadow transition-colors flex items-center justify-center gap-2"
            >
              {processing && <span className="animate-spin icon-[lucide--loader-2]" />}
              {contacto?.id ? 'Guardar Cambios' : 'Crear Contacto'}
            </button>

            <Link
              href={cancelUrl}
              className="w-full py-2 px-4 bg-white hover:bg-slate-50 text-slate-600 font-medium text-xs rounded-lg border border-slate-200 text-center block transition-colors"
            >
              Cancelar
            </Link>
          </div>
        </div>
      </div>

      {/* ÁREA DE CAMPOS DE FORMULARIO */}
      <div className="lg:col-span-3 space-y-6">

        {/* 1. FOTO DE PERFIL */}
        <section id="sec-foto" className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-2 flex items-center gap-2">
            <span className="icon-[lucide--camera] text-slate-500" />
            Fotografía de Perfil
          </h3>
          <div className="flex items-center gap-5">
            <div className="w-20 h-20 rounded-full border-2 border-slate-200 overflow-hidden bg-slate-100 flex items-center justify-center shrink-0">
              {photoPreview ? (
                <img src={photoPreview} alt="Vista previa" className="w-full h-full object-cover" />
              ) : (
                <span className="icon-[lucide--user] text-3xl text-slate-400" />
              )}
            </div>
            <div>
              <input
                type="file"
                accept="image/*"
                id="foto-upload"
                onChange={handleImageChange}
                className="hidden"
              />
              <label
                htmlFor="foto-upload"
                className="cursor-pointer inline-flex items-center gap-2 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
              >
                <span className="icon-[lucide--upload] text-sm" />
                Subir Imagen
              </label>
              <p className="text-[11px] text-slate-400 mt-1">Soporta JPG, PNG o WEBP. Máximo 2MB.</p>
              {getErrorMessage('foto') && <p className="text-xs text-red-500 mt-1">{getErrorMessage('foto')}</p>}
            </div>
          </div>
        </section>

        {/* 2. DATOS PERSONALES */}
        <section id="sec-identidad" className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-2 flex items-center gap-2">
            <span className="icon-[lucide--user-check] text-slate-500" />
            Datos Personales e Identificación
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Primer Nombre <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={data.primer_nombre}
                onChange={(e) => setData('primer_nombre', e.target.value)}
                className={`w-full border rounded-lg p-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 ${
                  getErrorMessage('primer_nombre') ? 'border-red-500 bg-red-50/20' : 'border-slate-300'
                }`}
              />
              {getErrorMessage('primer_nombre') && <span className="text-xs text-red-500 mt-1 block">{getErrorMessage('primer_nombre')}</span>}
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Segundo Nombre</label>
              <input
                type="text"
                value={data.segundo_nombre}
                onChange={(e) => setData('segundo_nombre', e.target.value)}
                className="w-full border border-slate-300 rounded-lg p-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Primer Apellido <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={data.primer_apellido}
                onChange={(e) => setData('primer_apellido', e.target.value)}
                className={`w-full border rounded-lg p-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 ${
                  getErrorMessage('primer_apellido') ? 'border-red-500 bg-red-50/20' : 'border-slate-300'
                }`}
              />
              {getErrorMessage('primer_apellido') && <span className="text-xs text-red-500 mt-1 block">{getErrorMessage('primer_apellido')}</span>}
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Segundo Apellido</label>
              <input
                type="text"
                value={data.segundo_apellido}
                onChange={(e) => setData('segundo_apellido', e.target.value)}
                className="w-full border border-slate-300 rounded-lg p-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Nº Empleado</label>
              <input
                type="text"
                value={data.numero_empleado}
                onChange={(e) => setData('numero_empleado', e.target.value)}
                className={`w-full border rounded-lg p-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 ${
                  getErrorMessage('numero_empleado') ? 'border-red-500 bg-red-50/20' : 'border-slate-300'
                }`}
              />
              {getErrorMessage('numero_empleado') && <span className="text-xs text-red-500 mt-1 block">{getErrorMessage('numero_empleado')}</span>}
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Abreviatura Título</label>
              <input
                type="text"
                placeholder="ej. Lic., Ing., Dr."
                value={data.abreviatura_titulo}
                onChange={(e) => setData('abreviatura_titulo', e.target.value)}
                className="w-full border border-slate-300 rounded-lg p-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Fecha de Nacimiento</label>
              <input
                type="date"
                value={data.fecha_nacimiento}
                onChange={(e) => setData('fecha_nacimiento', e.target.value)}
                className="w-full border border-slate-300 rounded-lg p-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

          </div>
        </section>

        {/* 3. ESTRUCTURA LABORAL */}
        <section id="sec-organizacion" className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-2 flex items-center gap-2">
            <span className="icon-[lucide--building-2] text-slate-500" />
            Estructura Laboral y Organización
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Empresa Principal</label>
              <select
                value={data.empresa_id}
                onChange={(e) => setData('empresa_id', e.target.value)}
                className="w-full border border-slate-300 rounded-lg p-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
              >
                <option value="">Selecciona Empresa</option>
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
                className="w-full border border-slate-300 rounded-lg p-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
              >
                <option value="">Selecciona Área</option>
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
                className="w-full border border-slate-300 rounded-lg p-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
              >
                <option value="">Selecciona Puesto</option>
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
                className="w-full border border-slate-300 rounded-lg p-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
              >
                <option value="">Selecciona Sede</option>
                {sedes.map((sede) => (
                  <option key={sede.id} value={sede.id}>{sede.nombre}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Jefe Directo</label>
              <select
                value={data.jefe_directo_id}
                onChange={(e) => setData('jefe_directo_id', e.target.value)}
                className="w-full border border-slate-300 rounded-lg p-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
              >
                <option value="">Sin Jefe Directo Asignado</option>
                {contactosJefes.map((jefe) => (
                  <option key={jefe.id} value={jefe.id}>{jefe.nombre_completo}</option>
                ))}
              </select>
            </div>

          </div>
        </section>

        {/* 4. MEDIOS DE CONTACTO */}
        <section id="sec-contacto" className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-6">
          <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-2 flex items-center gap-2">
            <span className="icon-[lucide--mail] text-slate-500" />
            Correos Electrónicos y Teléfonos
          </h3>

          {/* LISTA DE EMAILS */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">Correos Electrónicos</label>
              <button
                type="button"
                onClick={addEmail}
                className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold flex items-center gap-1"
              >
                <span className="icon-[lucide--plus] text-sm" /> Agregar Correo
              </button>
            </div>

            {data.emails.map((item: any, idx: number) => {
              const emailError = getErrorMessage(`emails.${idx}.email`);
              return (
                <div key={idx} className="p-3 border border-slate-200 rounded-lg bg-slate-50/50 space-y-2">
                  <div className="flex items-center gap-3">
                    <div className="flex-1">
                      <input
                        type="email"
                        placeholder="correo@ejemplo.com"
                        value={item.email}
                        onChange={(e) => handleEmailChange(idx, 'email', e.target.value)}
                        className={`w-full border rounded-lg p-2 text-sm outline-none bg-white focus:ring-2 focus:ring-indigo-500 ${
                          emailError ? 'border-red-500 bg-red-50/20' : 'border-slate-300'
                        }`}
                      />
                    </div>
                    {data.emails.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeEmail(idx)}
                        className="p-2 text-slate-400 hover:text-red-500 rounded-lg transition-colors"
                      >
                        <span className="icon-[lucide--trash-2] text-base" />
                      </button>
                    )}
                  </div>

                  <div className="flex items-center gap-6 text-xs text-slate-600">
                    <label className="flex items-center gap-1.5 cursor-pointer">
                      <input
                        type="radio"
                        name="email_principal"
                        checked={item.es_principal}
                        onChange={(e) => handleEmailChange(idx, 'es_principal', e.target.checked)}
                        className="text-indigo-600 focus:ring-indigo-500"
                      />
                      <span>Es Principal</span>
                    </label>

                    <label className="flex items-center gap-1.5 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={item.es_slack}
                        onChange={(e) => handleEmailChange(idx, 'es_slack', e.target.checked)}
                        className="rounded text-indigo-600 focus:ring-indigo-500"
                      />
                      <span>Vincular con Slack</span>
                    </label>
                  </div>

                  {emailError && <p className="text-xs text-red-500">{emailError}</p>}
                </div>
              );
            })}
          </div>

          {/* LISTA DE TELÉFONOS */}
          <div className="space-y-3 pt-2 border-t border-slate-100">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">Teléfonos de Contacto</label>
              <button
                type="button"
                onClick={addTelefono}
                className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold flex items-center gap-1"
              >
                <span className="icon-[lucide--plus] text-sm" /> Agregar Teléfono
              </button>
            </div>

            {data.telefonos.map((item: any, idx: number) => (
              <div key={idx} className="p-3 border border-slate-200 rounded-lg bg-slate-50/50 space-y-2">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-center">
                  <div className="sm:col-span-2">
                    <input
                      type="text"
                      placeholder="Número de teléfono (10 dígitos)"
                      value={item.telefono}
                      onChange={(e) => handleTelefonoChange(idx, 'telefono', e.target.value)}
                      className="w-full border border-slate-300 rounded-lg p-2 text-sm outline-none bg-white focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      placeholder="Ext."
                      value={item.extension || ''}
                      onChange={(e) => handleTelefonoChange(idx, 'extension', e.target.value)}
                      className="w-20 border border-slate-300 rounded-lg p-2 text-sm outline-none bg-white focus:ring-2 focus:ring-indigo-500"
                    />
                    {data.telefonos.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeTelefono(idx)}
                        className="p-2 text-slate-400 hover:text-red-500 rounded-lg transition-colors"
                      >
                        <span className="icon-[lucide--trash-2] text-base" />
                      </button>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-6 text-xs text-slate-600">
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="telefono_principal"
                      checked={item.es_principal}
                      onChange={(e) => handleTelefonoChange(idx, 'es_principal', e.target.checked)}
                      className="text-indigo-600 focus:ring-indigo-500"
                    />
                    <span>Es Principal</span>
                  </label>

                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={item.es_celular}
                      onChange={(e) => handleTelefonoChange(idx, 'es_celular', e.target.checked)}
                      className="rounded text-indigo-600 focus:ring-indigo-500"
                    />
                    <span>Celular (WhatsApp)</span>
                  </label>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* 5. FECHAS Y CONFIGURACIÓN */}
        <section id="sec-configuracion" className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-2 flex items-center gap-2">
            <span className="icon-[lucide--sliders] text-slate-500" />
            Estatus y Configuración de Visibilidad
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Fecha de Ingreso</label>
              <input
                type="date"
                value={data.fecha_ingreso}
                onChange={(e) => setData('fecha_ingreso', e.target.value)}
                className={`w-full border rounded-lg p-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 ${
                  getErrorMessage('fecha_ingreso') ? 'border-red-500 bg-red-50/20' : 'border-slate-300'
                }`}
              />
              {getErrorMessage('fecha_ingreso') && <span className="text-xs text-red-500 mt-1 block">{getErrorMessage('fecha_ingreso')}</span>}
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Fecha de Egreso</label>
              <input
                type="date"
                value={data.fecha_egreso}
                onChange={(e) => setData('fecha_egreso', e.target.value)}
                className={`w-full border rounded-lg p-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 ${
                  getErrorMessage('fecha_egreso') ? 'border-red-500 bg-red-50/20' : 'border-slate-300'
                }`}
              />
              {getErrorMessage('fecha_egreso') && <span className="text-xs text-red-500 mt-1 block">{getErrorMessage('fecha_egreso')}</span>}
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label className="flex items-center gap-2 p-2.5 rounded-lg border border-slate-200 hover:bg-slate-50 cursor-pointer">
              <input
                type="checkbox"
                checked={data.mostrar_en_directorio}
                onChange={(e) => setData('mostrar_en_directorio', e.target.checked)}
                className="rounded text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-xs font-medium text-slate-700">Mostrar en el directorio público</span>
            </label>

            <label className="flex items-center gap-2 p-2.5 rounded-lg border border-slate-200 hover:bg-slate-50 cursor-pointer">
              <input
                type="checkbox"
                checked={data.mostrar_en_cumpleanios}
                onChange={(e) => setData('mostrar_en_cumpleanios', e.target.checked)}
                className="rounded text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-xs font-medium text-slate-700">Mostrar en lista de cumpleaños</span>
            </label>

            <label className="flex items-center gap-2 p-2.5 rounded-lg border border-slate-200 hover:bg-slate-50 cursor-pointer">
              <input
                type="checkbox"
                checked={data.es_jefe}
                onChange={(e) => setData('es_jefe', e.target.checked)}
                className="rounded text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-xs font-medium text-slate-700">Marcar como Jefe de Equipo</span>
            </label>

            <label className="flex items-center gap-2 p-2.5 rounded-lg border border-slate-200 hover:bg-slate-50 cursor-pointer bg-red-50/30">
              <input
                type="checkbox"
                checked={data.esta_archivado}
                onChange={(e) => setData('esta_archivado', e.target.checked)}
                className="rounded text-red-600 focus:ring-red-500"
              />
              <span className="text-xs font-medium text-red-700">Archivar / Desactivar Contacto</span>
            </label>
          </div>
        </section>

      </div>
    </form>
  );
}