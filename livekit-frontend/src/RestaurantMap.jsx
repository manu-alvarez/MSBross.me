import React from 'react';

export const RestaurantMap = ({ highlightTable }) => {
    // Simulated table layout
    const tables = [
        { id: 1, x: 25, y: 30, type: '2-pax', zone: 'Terraza' },
        { id: 2, x: 75, y: 30, type: '2-pax', zone: 'Terraza' },
        { id: 3, x: 25, y: 70, type: '4-pax', zone: 'Interior' },
        { id: 4, x: 75, y: 70, type: '4-pax', zone: 'Interior' },
        { id: 5, x: 50, y: 50, type: '6-pax', zone: 'Centro' },
    ];

    return (
        <div className="glass-panel" style={{
            padding: '24px',
            animation: 'fadeInLeft 0.5s ease-out 0.2s',
            animationFillMode: 'both',
            color: 'var(--text-primary)',
            width: '380px',
            marginTop: '16px'
        }}>
            <h3 style={{
                fontFamily: '"Outfit", sans-serif',
                fontSize: '1.4rem',
                fontWeight: 700,
                color: 'var(--primary-main)',
                borderBottom: '1px solid rgba(255,255,255,0.1)',
                paddingBottom: '12px',
                marginBottom: '20px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
            }}>
                <span style={{fontSize: '1.2rem'}}>📍</span> Mapa de Mesas
            </h3>

            <div style={{
                position: 'relative',
                width: '100%',
                aspectRatio: '16/10',
                background: 'linear-gradient(135deg, rgba(20,20,30,0.8) 0%, rgba(10,10,15,0.9) 100%)',
                border: '1px solid rgba(255,255,255,0.05)',
                borderRadius: '12px',
                overflow: 'hidden',
                boxShadow: 'inset 0 0 20px rgba(0,0,0,0.5)'
            }}>
                {/* Floor layout base */}
                <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '40%', borderBottom: '1px dashed rgba(255,255,255,0.1)' }} />
                
                {/* Floor indicators */}
                <div style={{ position: 'absolute', top: '12%', left: '12px', color: 'rgba(255,255,255,0.2)', fontSize: '0.7rem', letterSpacing: '3px', fontWeight: 700 }}>TERRAZA</div>
                <div style={{ position: 'absolute', bottom: '12%', left: '12px', color: 'rgba(255,255,255,0.2)', fontSize: '0.7rem', letterSpacing: '3px', fontWeight: 700 }}>INTERIOR</div>

                {tables.map(table => {
                    const isHighlighted = highlightTable && parseInt(highlightTable) === table.id;
                    return (
                        <div
                            key={table.id}
                            style={{
                                position: 'absolute',
                                left: `${table.x}%`,
                                top: `${table.y}%`,
                                transform: 'translate(-50%, -50%)',
                                width: table.type.startsWith('6') ? '60px' : '40px',
                                height: '28px',
                                background: isHighlighted ? 'var(--primary-main)' : 'rgba(255,255,255,0.05)',
                                border: isHighlighted ? '2px solid #fff' : '1px solid rgba(255,255,255,0.2)',
                                borderRadius: table.type.startsWith('2') ? '50%' : '6px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                color: isHighlighted ? '#000' : 'rgba(255,255,255,0.6)',
                                fontWeight: 'bold',
                                fontSize: '0.85rem',
                                boxShadow: isHighlighted ? '0 0 20px rgba(139, 92, 246, 0.6), inset 0 0 10px rgba(255,255,255,0.5)' : 'none',
                                transition: 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                                zIndex: isHighlighted ? 10 : 1
                            }}
                        >
                            {table.id}
                        </div>
                    );
                })}
            </div>
            
            {highlightTable && (
                <div style={{ 
                    marginTop: '20px', 
                    padding: '16px', 
                    background: 'rgba(139, 92, 246, 0.1)', 
                    borderRadius: '12px',
                    border: '1px solid rgba(139, 92, 246, 0.3)',
                    animation: 'fadeInUp 0.3s ease-out'
                }}>
                    <p style={{ margin: 0, fontSize: '0.95rem', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ color: 'var(--primary-main)', animation: 'pulse 1.5s infinite'}}>●</span>
                        Nikolina sugiere la <strong>Mesa {highlightTable}</strong>
                    </p>
                </div>
            )}
        </div>
    );
};
